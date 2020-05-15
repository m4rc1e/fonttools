from fontTools.otlLib.unbuilder import *
from fontTools.ttLib import TTFont
import sys
from pprint import pprint
import subprocess
import logging

"""

"""

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def all_glyphs(ttfont, results, iterations=2, ignore_features=["aalt", "c2sc"]):
    """
    in/out:

    {"f.alt": {"input": "f", "features": ["salt"], "lang": "latn", "script": "LATN"}}
    {"f_f_i": {"input": "ffi", "features": ["liga"], "lang": "latn", "script: "LATN"}}
    

    Technique:
    - Do following to DFLT script first, then repeat on other scripts
      - get script default feature indexes
      - iter through each lookup mention in each feature_idx
      - Ignore features in ignore_features
      - iter through each subtable in each lookup
        - if v not in results:
          - make join found inputs using results e.g i = f + f = join(results['f'] + results['f'])
          - put back into results results[v] = i
    """
    if iterations == 0:
        return

    gsub = unbuildTable(ttfont["GSUB"].table)

    processed = set()
    lk_order = []
    for script in gsub['scripts']:
        lang_features = [gsub["features"][i] for i in script["DefaultLangSys"]["FeatureIndices"]]
        lang_features.sort(key=lambda k: k["lookup_indices"])
        for feature in lang_features:
            if feature["tag"] in ignore_features:
                continue
            for l_idx in feature['lookup_indices']:
                log.debug("processing lookup {}".format(l_idx))
                lk_order.append(l_idx)
                if l_idx in processed:
                    continue
                lookup = gsub["lookups"][l_idx]
                _process_lookup(lookup, results, feature['tag'], script['tag'], "dflt")
                processed.add(l_idx)
    all_glyphs(ttfont, results, iterations-1, ignore_features)
    return



def _process_lookup(lookup, results, feature_tag, script_tag, lang_tag):
    if lookup["type"] == 1:
        _process_singlesub(lookup, results, feature_tag, script_tag, lang_tag)
    elif lookup["type"] == 2:
        _process_multisub(lookup, results, feature_tag, script_tag, lang_tag)
    elif lookup["type"] == 4:
        _process_ligasub(lookup, results, feature_tag, script_tag, lang_tag)
    elif lookup["type"] == 5:
        _process_context(lookup, results, feature_tag, script_tag, lang_tag)
    elif lookup["type"] == 6:
        _process_chainingcontext(lookup, results, feature_tag, script_tag, lang_tag)


def _process_singlesub(lookup, results, feature, script, lang):
    for subtable in lookup["subtables"]:
        for _in, _out in subtable["subs"].items():
            if _in in results and _out not in results:
                new = {}
                new["input"] = results[_in]["input"]
                new["features"] = [feature] + results[_in]["features"]
                new["lang"] = lang
                new["script"] = script
                results[_out] = new


def _process_multisub(lookup, results, feature, script, lang):
    pass


def _process_ligasub(lookup, results, feature, script, lang):
    for subtable in lookup["subtables"]:
        for _in, _out in subtable["ligatures"].items():
            new = {}
            new["input"] = ""
            new["features"] = [feature]
            new["lang"] = lang
            new["script"] = script
            for glyph in _in:
                if glyph in results:
                    r = results[glyph]
                    new["input"] += r["input"]
                    new["features"] += r["features"]
            results[_out] = new


def _process_context(lookup, results, feature, script, lang):
    for subtable in lookup["subtables"]:
        if  subtable["format"] == 1:
            _process_context1(lookup, results, feature, script, lang)
        elif  subtable["format"] == 2:
            _process_context2(lookup, results, feature, script, lang)
        elif subtable["format"] == 3:
            _process_context3(lookup, results, feature, script, lang)


def _process_context1(lookup, results, feature, script, lang):
    for subtable in lookup["subtables"]:
        for rule in subtable["rules"]:
            new = {'features': [feature], "input": "", "lang": lang, "script": script}
            for glyph in rule["input"]:
                new["input"] += results[glyph]["input"]
                new["features"] += results[glyph]["features"]
            results[tuple(rule["input"])] = new


def _process_context2(lookup, results, feature, script, lang):
    for subtable in lookup["subtables"]:
        for rule in subtable["rules"]:
            if not len([c for c in rule['input'] if c in subtable['classes']]) == len(rule['input']):
                continue
            combos = [subtable["classes"][c] for c in rule["input"]]
            permutations = perms(combos)
            skipped = 0
            for perm in permutations:
                if not has_all_glyphs(perm, results):
                    skipped+=1
                    continue
                new = {'features': [feature], "input": "", "lang": lang, "script": script}
                for glyph in perm:
                    new["input"] += results[glyph]["input"]
                    new["features"] += results[glyph]["features"]
                results[tuple(perm)] = new


def _process_context3(lookup, results, feature, script, lang):
    # TODO must add to spec first
    pass

def _process_chainingcontext(lookup, results, feature, script, lang):
    for subtable in lookup["subtables"]:
        if subtable["format"] == 1:
            _process_chainingcontext1(lookup, results, feature, script, lang)
        elif subtable["format"] == 2:
            _process_chainingcontext2(lookup, results, feature, script, lang)
        elif subtable["format"] == 3:
            _process_chainingcontext3(lookup, results, feature, script, lang)


def _process_chainingcontext1(lookup, results, feature, script, lang, limit=100):
    for subtable in lookup["subtables"]:
        for rule in subtable["rules"]:
            new = {'features': [feature], "input": "", "lang": lang, "script": script}
            for k in ["backtrack", "input", "lookahead"]:
                for glyph in rule[k]:
                    new["input"] += results[glyph]["input"]
                    new["features"] += results[glyph]["features"]
            results[tuple(rule["input"])] = new


def _process_chainingcontext2(lookup, results, feature, script, lang, limit=100):
    for subtable in lookup["subtables"]:
        for rule in subtable["rules"]:
            backtrack = [subtable["backtrack_classes"][c] for c in rule["backtrack"]]
            input_ = [subtable["input_classes"][c] for c in rule["input"]]
            lookahead = [subtable["lookahead_classes"][c] for c in rule["lookahead"]]
            permutations = perms(backtrack+input_+lookahead)
            for perm in permutations:
                if not has_all_glyphs(perm, results):
                    continue
                new = {'features': [feature], "input": "", "lang": lang, "script": script}
                for glyph in perm:
                    new["input"] += results[glyph]["input"]
                    new["features"] += results[glyph]["features"]
                results[tuple(perm)] = new


def _process_chainingcontext3(lookup, results, feature, script, lang, limit=1):
    for subtable in lookup["subtables"]:
        # Process the reference lookups first
        _process_lookup
        backtrack = subtable["backtrack"][:limit] if subtable["backtrack"] else []
        lookahead = subtable["lookahead"][:limit] if subtable["lookahead"] else []
        combos = backtrack + subtable["input"] + lookahead
        permutations = perms(combos)
        skipped = 0
        for perm in permutations:
            if not has_all_glyphs(perm, results):
                skipped+=1
                continue
            new = {'features': [feature], "input": "", "lang": lang, "script": script}
            for glyph in perm:
                new["input"] += results[glyph]["input"]
                new["features"] += results[glyph]["features"]
            results[tuple(perm)] = new


def has_all_glyphs(perm, results):
    for glyph in perm:
        if glyph not in results:
            log.debug(f"Missing {glyph}")
            return False
    return True


def perms(a, s=0, p=[], res=[]):
    """[[1,2][3,4]] --> [[1,3], [1,4], [2,3], [2,4]]"""
    if len(p) == len(a):
        res.append(p[:])
        return res
    for g in range(s, len(a)):
        for l in range(len(a[g])):
            p.append(a[g][l])
            perms(a, g+1, p, res)
            p.pop()
    return res


def main():
    ttfont = TTFont(sys.argv[1])

    results = {v: {
        "input": chr(k),
        "features": [],
        "lang": "dflt",
        "script": "DFLT"
    } for k,v in ttfont.getBestCmap().items()}
    
    a = len(results)
    all_glyphs(ttfont, results)
    pprint(results, open("/Users/marcfoley/Desktop/COMBOS.txt", "w"))

#    for glyph in glyphs:
#        if isinstance(glyph, tuple):
#            reorder_character_seq(font, glyphs[glyph])
#    i = " ".join([g["input"] for g in glyphs.values()]) 
#    print(i)
#    for r,o in glyphs.items():
#        print(o)
#    print(len(glyphs))

if __name__ == "__main__":
    main()
#    f = TTFont('/Users/marcfoley/Type/fonts/ofl/notosans/NotoSans-Regular.ttf')
#    for i, lk in enumerate(f['GSUB'].table.LookupList.Lookup):
#        print(i, lk.LookupType, lk.SubTable[0].Format)
#    pprint(unbuildLookup(f['GSUB'].table.LookupList.Lookup[22])) # 76

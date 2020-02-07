from fontTools.otlLib.unbuilder import *
from fontTools.ttLib import TTFont
import sys
from pprint import pprint
import subprocess

"""

"""

def all_glyphs(ttfont, ignore_features=["aalt", "c2sc"]):
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
    results = {v: {
        "input": chr(k),
        "features": [],
        "lang": "dflt",
        "script": "DFLT"
    } for k,v in ttfont.getBestCmap().items()}
    processed = set()

    gsub = unbuildGSUB(ttfont["GSUB"].table)

    # attempt just gsub lookupType 1 with DFLT script
    for script in gsub['scripts']:
        lang_features = [gsub["features"][i] for i in script["DefaultLangSys"]["FeatureIndices"]]
        lang_features.sort(key=lambda k: k["lookup_indices"])
        for feature in lang_features:
            if feature["tag"] in ignore_features:
                continue
            for l_idx in feature['lookup_indices']: # todo change
                if l_idx in processed:
                    continue
                lookup = gsub["lookups"][l_idx]

                if lookup["type"] == 1:
                    _process_singlesub(lookup, results, feature['tag'], script["tag"], "dflt")
                if lookup["type"] == 2:
                    _process_multisub(lookup, results, feature['tag'], script['tag'], "dflt")
                elif lookup["type"] == 4:
                    _process_ligasub(lookup, results, feature["tag"], script["tag"], "dflt")
#                if lookup["type"] == 5:
#                    _process_context(lookup, results, feature['tag'], script['tag'], "dflt")
                elif lookup["type"] == 6:
                    _process_chainingcontext(lookup, results, feature['tag'], script["tag"], "dflt")
                processed.add(l_idx)
    for lk in gsub['lookups']:
        print(lk["type"])
    return results


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
            else:
                print("MISSING", _in, feature)


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


def _process_chainingcontext(lookup, results, feature, script, lang):
    for subtable in lookup["subtables"]:
        if  subtable["format"] == 3:
            _process_chainingcontext3(lookup, results, feature, script, lang)


def _process_context(lookup, results, feature, script, lang):
    for subtable in lookup["subtables"]:
        if  subtable["format"] == 2:
            _process_context2(lookup, results, feature, script, lang)


def _process_context2(lookup, results, feature, script, lang):
    for subtable in lookup["subtables"]:
        if subtable['format'] == 2:
            from pprint import pprint
            pprint(subtable)


def _process_chainingcontext3(lookup, results, feature, script, lang, limit=10000):
    for subtable in lookup["subtables"]:
        # we only want to append just the first and last glyph of the lookahead
        # and back track contexts due to run time.
        backtrack = subtable["backtrack"][:limit] if subtable["backtrack"] else []
        lookahead = subtable["lookahead"][:limit] if subtable["lookahead"] else []
        combos = backtrack + subtable["input"] + lookahead
        permutations = perms(combos)
        skipped = 0
        for perm in permutations:
            if not has_all_glyphs(perm, results):
                print('skipping', perm)
                skipped+=1
                continue
            new = {'features': [feature], "input": "", "lang": lang, "script": script}
            for glyph in perm:
                new["input"] += results[glyph]["input"]
                new["features"] += results[glyph]["features"]
            results[tuple(perm)] = new
    print(skipped,'skipped')


def has_all_glyphs(perm, results):
    for glyph in perm:
        if glyph not in results:
            print(glyph)
            return False
    return True


def perms(a, s=0, p=[], res=[]):
    if len(p) == len(a):
        res.append(p[:])
        return res
    for g in range(s, len(a)):
        for l in range(len(a[g])):
            p.append(a[g][l])
            perms(a, g+1, p, res)
            p.pop()
    return res


def reorder_character_seq(hbfont, seq):
    hb.ot_font_set_funcs(font)

    buf = hb.Buffer()

    buf.add_str(seq['input'])
    buf.guess_segment_properties()

    features = {"kern": True, "liga": True}
    hb.shape(font, buf, features)

    infos = buf.glyph_infos
    if len([i for i in infos if i.codepoint == 188]) > 0:
        seq['input'] = seq['input'][1:] + seq['input'][0]


if __name__ == "__main__":
    import uharfbuzz as hb
    ttfont = TTFont(sys.argv[1])
    with open(sys.argv[1], 'rb') as fontfile:
        fontdata = fontfile.read()
    face = hb.Face(fontdata)
    font = hb.Font(face)

    glyphs = all_glyphs(ttfont)
    for glyph in glyphs:
        if isinstance(glyph, tuple):
            reorder_character_seq(font, glyphs[glyph])
    i = " ".join([g["input"] for g in glyphs.values()]) 
    print(i)

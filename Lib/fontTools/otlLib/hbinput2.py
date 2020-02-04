from fontTools.otlLib.unbuilder import *
from fontTools.ttLib import TTFont
import sys
from pprint import pprint

"""
TODO:

- Put formats back in subtables
- Relook at Script, Feature, Lookup unbuilds. See Cosimo doc and restudy spec.
- Unbuild FeatureParams table


feature param table:
    version: int
    nameid: str

"""

def all_glyphs(ttfont, ignore_features=["aalt"]):
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
        "lang": None,
        "script": None
    } for k,v in ttfont.getBestCmap().items()}

    gsub = unbuildGSUB(ttfont["GSUB"].table)
    # print(results)
    pprint(gsub)

    # attempt just gsub lookupType 1 with DFLT script
#    for script in gsub['scripts']:
#        if script['tag'] != "DFLT":
#            continue
#        for f_idx in script["DefaultFeatureIndexs"]:
#            feature = gsub["features"][f_idx]
#            if feature["tag"] in ignore_features:
#                continue
#            for l_idx in feature['lookups']: # TODO check if there is a lookup order array!!!
#                lookup = gsub["lookups"][l_idx]
#
#                if lookup["type"] == 1:
#                    _process_singlesub(lookup, results, feature['tag'], script["tag"], "dflt")
#                if lookup["type"] == 4:
#                    _process_ligasub(lookup, results, feature["tag"], script["tag"], "dflt")
#
    #for k,v in results.items():
        # pass
        # print(k, v)


def _process_singlesub(lookup, results, feature, script, lang):
    for subtable in lookup["subtables"]:
        for _in, _out in subtable.items():
            if _in in results:
                new = {}
                new["input"] = results[_in]["input"]
                new["features"] = [feature] + results[_in]["features"]
                new["lang"] = lang
                new["script"] = script
                results[_out] = new
            else:
                print("MISSING", _in, feature)


def _process_ligasub(lookup, results, feature, script, lang):
    for subtable in lookup["subtables"]:
        for _in, _out in subtable.items():
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

if __name__ == "__main__":
    ttfont = TTFont(sys.argv[1])
    glyphs = all_glyphs(ttfont)


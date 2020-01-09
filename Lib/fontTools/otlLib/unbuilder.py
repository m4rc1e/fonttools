from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables


def unbuildCoverage(coverage):
    return coverage.glyphs


def unbuildLookup(lookup):
    results = []
    for subtable in lookup.SubTable:
        for subtable_type, unbuilder in UNBUILD_MAP.items():
            if isinstance(subtable, subtable_type):
                results.append(unbuilder(subtable))
    return results


def unbuildGSUB(table, unbuild_nested=False):
    # TODO
    lookups = [unbuildLookup(l) for l in table.LookupList.Lookup]
    return lookups

# GSUB


def unbuildSingleSubstSubtable(singleSubst):
    return singleSubst.mapping


def unbuildMultipleSubstSubtable(multipleSubstSubtable):
    return multipleSubstSubtable.mapping


def unbuildAlternateSubstSubtable(alternateSubstSubtable):
    return alternateSubstSubtable.alternates


def unbuildLigatureSubstSubtable(ligatureSubstSubtable):
    results = {}
    for k, ligatures in ligatureSubstSubtable.ligatures.items():
        for ligature in ligatures:
            results[tuple([k] + ligature.Component)] = ligature.LigGlyph
    return results



def unbuildClassDef(classDef):
    results = {}
    for k, v in classDef.classDefs.items():
        if v not in results:
            results[v] = []
        results[v].append(k)
    return results


def unbuildContSubtable(subtable):
    results = {"input": [], "lookup_idx": []}
    if subtable.Format == 1:
        # TODO do we want to store the inputs and lookup_idxs as two seperate lists?
        # or do we want {"input1": output1...}
        """
        Notes on Format 5.1: Simple Glyph Contexts
        https://docs.microsoft.com/en-us/typography/opentype/spec/gsub#51-context-substitution-format-1-simple-glyph-contexts
        Swap each glyph in a context sequence with another glyph.
        Individual glyphs seems to get swapped using a lookup for each glyph.

        - Coverage table holds the first glyph for each context
        - Coverage table does not contain duplicates glyphs
        - Each glyph in the coverage table points to its own SubRuleSet table which defines SubRules.
          This extra table allows us to map multiple contexts to a single glyph
        - SubRules contain the rest of the glyphs in the context
        - SubRules also contain a lookup table
        - SubRule lookup table contains a lookup for each glyph in the context.

        """
        for prefix in subtable.Coverage.glyphs:
            for ruleset in subtable.SubRuleSet:
                for rule in ruleset.SubRule:
                    glyph_input = [prefix] + r.Input
                    lookup_idxs = [r.LookupListIndex for r in rule.SubstLookupRecord]
                    results['input'].append(glyph_input)
                    results['lookup_idx'].append(lookup_idxs)

    if subtable.Format == 2:
        # TODO write function to unbuild ClassDefs
        prefix = subtable.Coverage.glyphs
        classes = unbuildClassDef(subtable.ClassDef)
        for ruleset in subtable.SubClassSet:
            if ruleset is None:
                continue
            for rule in ruleset.SubClassRule:
                c = [classes[r] for r in rule.Class]
                glyph_input = [prefix] + c
                lookup_idxs = [r.LookupListIndex for r in rule.SubstLookupRecord]
                results['input'].append(glyph_input)
                results['lookup_idx'].append(lookup_idxs)
    # TODO add Format 3
    return results


def unbuildChainContSubtable(subtable):
    results = {"lookahead": [], "backtrack": [], "lookup_idx": [], "input": []}
    if subtable.Format == 1:
        # Just padauk uses this Format
        for set_ in subtable.ChainSubRuleSet:
            for rule in set_.ChainSubRule:
                results["lookahead"].append(rule.LookAhead)
                results["backtrack"].append(rule.Backtrack)
                results["input"].append(rule.Input)
                for record in rule.SubstLookupRecord:
                    results["lookup_idx"].append(record.LookupListIndex)

    elif subtable.Format == 2:
        backtrack_classes = unbuildClassDef(subtable.BacktrackClassDef)
        lookahead_classes = unbuildClassDef(subtable.LookAheadClassDef)
        for set_ in subtable.ChainSubClassSet:
            if not set_:
                continue
            idxs, lookaheads, backtracks = [], [], []
            for rule in set_.ChainSubClassRule:
                results["input"].append(rule.Input)
                for record in rule.SubstLookupRecord:
                    idxs.append(record.LookupListIndex)
                for backtrack in rule.Backtrack:
                    backtracks.append(tuple(backtrack_classes[backtrack]))
                for lookahead in rule.LookAhead:
                    lookaheads.append(tuple(lookahead_classes[lookahead]))

                results["lookup_idx"].append(idxs)
                results["backtrack"].append(backtracks)
                results["lookahead"].append(lookaheads)
                idxs, lookaheads, backtracks = [], [], []

    elif subtable.Format == 3:
        for record in subtable.SubstLookupRecord:
            results['lookup_idx'].append(record.LookupListIndex)
        for coverage in subtable.LookAheadCoverage:
            results["lookahead"].append(tuple(coverage.glyphs))
        for coverage in subtable.BacktrackCoverage:
            results["backtrack"].append(tuple(coverage.glyphs))
    else:
        raise NotImplemented("Format {} is not supported".format(subtable.Format))
    return results




# GPOS


def unbuildAnchor(anchor):
    result = {}
    if not anchor:
        return None
    result["x"] = anchor.XCoordinate
    result["y"] = anchor.YCoordinate
    if hasattr(anchor, "AnchorPoint"):
        result["point"] = anchor.AnchorPoint
    if hasattr(anchor, "XDeviceTable"):
        result["deviceX"] = anchor.XDeviceTable
    if hasattr(anchor, "YDeviceTable"):
        result["deviceY"] = anchor.YDeviceTable
    return result


def unbuildBaseArray(baseArray):
    if not baseArray:
        return None
    return [unbuildBaseRecord(r) for r in baseArray.BaseRecord]


def unbuildBaseRecord(baseRecord):
    """otTables.BaseRecord --> [{"x": 10, "y": 10}, {"x": 20, "y": 20}, ...]"""
    if not baseRecord:
        return None
    return [unbuildAnchor(a) for a in baseRecord.BaseAnchor]


def unbuildComponentRecord(componentRecord):
    """otTables.ComponentRecord --> [{"x": 10, "y": 10}, {"x": 20, "y": 20}, ...]"""
    if not componentRecord:
        return None
    return [unbuildAnchor(a) for a in componentRecord.LigatureAnchor]


def unbuildCursivePosSubtable(cursivePos):
    """otTables.CursivePos --> {"alef": ({"x": 10, "y": 10}, {"x": 100, "y": 100})}"""
    results = {}
    for glyph, rec in zip(cursivePos.Coverage.glyphs, cursivePos.EntryExitRecord):
        results[glyph] = (unbuildAnchor(rec.EntryAnchor), unbuildAnchor(rec.ExitAnchor))
    return results


def unbuildDevice(device):
    """otTables.Device --> {8:+1, 10:-3, ...}"""
    sizes = range(device.StartSize, device.EndSize + 1)
    deltas = device.DeltaValue
    return dict(zip(sizes, deltas))


def unbuildLigatureArray(ligatureArray):
    return [unbuildLigatureAttach(r) for r in ligatureArray.LigatureAttach]


def unbuildLigatureAttach(ligatureAttach):
    return [unbuildComponentRecord(c) for c in ligatureAttach.ComponentRecord]


def unbuildMarkArray(markArray):
    return [unbuildMarkRecord(r) for r in markArray.MarkRecord]


def unbuildMarkBasePos(markBasePos):
    return [unbuildMarkBasePosSubtable(markBasePos)]


def unbuildMarkBasePosSubtable(markBasePos):
    mark_glyphs = unbuildCoverage(markBasePos.MarkCoverage)
    mark_array = unbuildMarkArray(markBasePos.MarkArray)
    marks = dict(zip(mark_glyphs, mark_array))

    base_glyphs = unbuildCoverage(markBasePos.BaseCoverage)
    base_array_ = unbuildBaseArray(markBasePos.BaseArray)
    # [[None, {"x": 1, "y": 1}], [{"x": 1, "y": 1}]] -->
    # [{1: {"x": 1, "y": 1}}, {0, {"x": 1, "y": 1}}]
    base_array = []
    for record in base_array_:
        base_array.append({idx: a for idx, a in enumerate(record) if a})
    bases = dict(zip(base_glyphs, base_array))
    return {"marks": marks, "bases": bases}


def unbuildMarkLigPosSubtable(markLigPos):
    mark_glyphs = unbuildCoverage(markLigPos.MarkCoverage)
    mark_array = unbuildMarkArray(markLigPos.MarkArray)
    marks = dict(zip(mark_glyphs, mark_array))

    lig_glyphs = unbuildCoverage(markLigPos.LigatureCoverage)
    lig_array_ = unbuildLigatureArray(markLigPos.LigatureArray)
    lig_array = []
    for lig in lig_array_:
        lig_attach = []
        for comp in lig:
            lig_attach.append({idx: a for idx, a in enumerate(comp) if a})
        lig_array.append(lig_attach)
    ligs = dict(zip(lig_glyphs, lig_array))
    return {"marks": marks, "ligs": ligs}


def unbuildMarkRecord(markRecord):
    return markRecord.Class, unbuildAnchor(markRecord.MarkAnchor)


def unbuildMark2Record(mark2Record):
    return [unbuildAnchor(a) for a in mark2Record.Mark2Anchor]


def unbuildPairPosSubtable(pairPosSubtable):
    if pairPosSubtable.Format == 1:
        return unbuildPairPosGlyphsSubtable(pairPosSubtable)
    if pairPosSubtable.Format == 2:
        return unbuildPairPosClassesSubtable(pairPosSubtable)


def unbuildPairPosClassesSubtable(pairPosClassesSubtable):
    results = {}
    coverage = unbuildCoverage(pairPosClassesSubtable.Coverage)
    p = pairPosClassesSubtable
    for glyph in set(coverage) - set(p.ClassDef1.classDefs):
        p.ClassDef1.classDefs[glyph] = 0

    # See builder.ClassDefBuilder.classes for how this is implemented
    class1 = {}
    for glyph, class_ in p.ClassDef1.classDefs.items():
        if class_ not in class1:
            class1[class_] = []
        class1[class_].append(glyph)
        class1[class_] = sorted(class1[class_])

    class2 = {}
    for glyph, class_ in p.ClassDef2.classDefs.items():
        if class_ not in class2:
            class2[class_] = []
        class2[class_].append(glyph)
        class2[class_] = sorted(class2[class_])
    class2[0] = []

    for idx1, c1 in enumerate(p.Class1Record):
        for idx2, c2 in enumerate(c1.Class2Record):
            vals = (unbuildValue(c2.Value1), unbuildValue(c2.Value2))
            if not any([vals[0], vals[1]]):
                continue
            results[tuple(class1[idx1]), tuple(class2[idx2])] = vals
    return results


def unbuildPairPosGlyphsSubtable(subtable):
    results = {}
    glyphs1 = {idx: glyph for idx, glyph in enumerate(subtable.Coverage.glyphs)}
    for p_idx, pairSet in enumerate(subtable.PairSet):
        for record in pairSet.PairValueRecord:
            glyph1, glyph2 = glyphs1[p_idx], record.SecondGlyph
            val1, val2 = unbuildValue(record.Value1), unbuildValue(record.Value2)
            results[(glyph1, glyph2)] = (val1, val2)
    return results


def unbuildSinglePosSubtable(singlePos):
    """otTables.SinglePos --> {glyphName: {"XPlacement: 100, "YPlacement": 100}}"""
    result = {}
    if singlePos.Format == 1:
        for glyph in singlePos.Coverage.glyphs:
            if not glyph in result:
                result[glyph] = unbuildValue(singlePos.Value)
    if singlePos.Format == 2:
        for glyph, value in zip(singlePos.Coverage.glyphs, singlePos.Value):
            result[glyph] = unbuildValue(value)
    return result


def unbuildValue(valueRecord):
    result = {}
    if hasattr(valueRecord, "XPlacement"):
        result["XPlacement"] = valueRecord.XPlacement
    if hasattr(valueRecord, "YPlacement"):
        result["YPlacement"] = valueRecord.YPlacement
    if hasattr(valueRecord, "XAdvance"):
        result["XAdvance"] = valueRecord.XAdvance
    if hasattr(valueRecord, "YAdvance"):
        result["YAdvance"] = valueRecord.YAdvance
    if not result:
        return None
    return result


# GDEF


def unbuildAttachList(attachList):
    """otTables.AttachList --> {"glyphName": [4, 23]}"""
    if not attachList:
        return None
    coverage = unbuildCoverage(attachList.Coverage)
    attachPoint = [unbuildAttachPoint(p) for p in attachList.AttachPoint]
    return dict(zip(coverage, attachPoint))


def unbuildAttachPoint(attachPoint):
    """otTables.AttachPoint --> [4, 23, 41]"""
    if not attachPoint:
        return None
    return attachPoint.PointIndex


def unbuildCaretValueForCoord(caretValue):
    """otTables.CaretValue --> 500"""
    return caretValue.Coordinate


def unbuildCaretValueForPoint(caretValue):
    """otTables.CaretValue, format 2 --> 4"""
    return caretValue.CaretValuePoint


def unbuildLigCaretList(ligCaretList):
    """otTables.LigCaretList --> {"f_f_i": [300, 600]}, {"c_t": [28]}"""
    if not ligCaretList:
        return None
    glyphs = unbuildCoverage(ligCaretList.Coverage)
    carets = [unbuildLigGlyph(c) for c in ligCaretList.LigGlyph]
    return dict(zip(glyphs, carets))


def unbuildLigGlyph(ligGlyph):
    """otTables.LigGlyph; None for empty coords/points --> ([500], [4])"""
    if not ligGlyph:
        return None
    results = []
    for caret in ligGlyph.CaretValue:
        if hasattr(caret, "Coordinate"):
            results.append(unbuildCaretValueForCoord(caret))
        if hasattr(caret, "CaretValuePoint"):
            results.append(unbuildCaretValueForPoint(caret))
    return results


def unbuildMarkGlyphSetsDef(markGlyphSetsDef):
    """otTables.MarkGlyphSetsDef --> [{"acute","grave"}, {"caron","grave"}]"""
    if not markGlyphSetsDef:
        return None
    return [set(unbuildCoverage(m)) for m in markGlyphSetsDef.Coverage]


UNBUILD_MAP = {
    # GSUB
    otTables.SingleSubst: unbuildSingleSubstSubtable,
    otTables.MultipleSubst: unbuildMultipleSubstSubtable,
    otTables.AlternateSubst: unbuildAlternateSubstSubtable,
    otTables.LigatureSubst: unbuildLigatureSubstSubtable,
    otTables.ChainContextSubst: unbuildChainContSubtable,
    # GPOS
    otTables.SinglePos: unbuildSinglePosSubtable,
    otTables.PairPos: unbuildPairPosSubtable,
    otTables.CursivePos: unbuildCursivePosSubtable,
    otTables.MarkBasePos: unbuildMarkBasePosSubtable,
    otTables.MarkLigPos: unbuildMarkLigPosSubtable,
}

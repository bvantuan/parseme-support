#! /usr/bin/env python3

r"""
    This is a small library for reading and interpreting the parseme TSV format.

    PARSEME TSV files contain these 4 fields:
    * WordID: an integer (starts at 1)
    * Surface: a string
    * NoSpace: "nsp"  -- or EMPTY
    * MWEs: a list of MWE codes (e.g. "1:LVC;3:ID;4:LVC")  -- or EMPTY

    Additionally, a POS optional field (str or EMPTY) may be present.

    EMPTY columns may contain "_" or "".
"""


import collections

EMPTY = ["_", ""]


class TSVSentence(list):
    r"""A list of Words."""

    def mwe_infos(self):
        r"""Return a dict {mwe_id: MWEInfo} for all MWEs in this sentence."""
        mwe_infos = {}
        for word_index, word in enumerate(self):
            for mwe_id, mwe_categ in word.mwes_id_categ():
                mwe_info = mwe_infos.setdefault(mwe_id, MWEInfo(mwe_categ, []))
                mwe_info.word_indexes.append(word_index)
        return mwe_infos


class MWEInfo(collections.namedtuple('MWEInfo', 'category word_indexes')):
    r"""Represents all MWEs in a sentence.
    CAREFUL: word indexes start at 0 (not at 1, as in the WordIDs).

    Arguments:
    @type category: str
    @type word_indexes: list[int]
    """
    pass


class TSVWord(collections.namedtuple('Word', 'surface nsp mwe_code pos')):
    r"""Represents a word in the TSV file.

    Arguments:
    @type surface: str
    @type nsp: bool
    @type mwe_code: list[str]
    @type pos: Optional[str]
    """
    def mwes_id_categ(self):
        r"""For each MWE code in `self.mwe_code`, yield an (id, categ) pair.
        @rtype Iterable[(int, Optional[str])]
        """
        for mwe_str in self.mwe_code:
            split = mwe_str.split(":")
            mwe_id = int(split[0])
            mwe_categ = (split[1] if len(split) > 1 else None)
            yield mwe_id, mwe_categ


############################################################

def iter_tsv_sentences(fileobj):
    r"""Yield `TSVSentence` instances for all sentences in the underlying PARSEME TSV file."""
    n_fields = len(fileobj.buffer.peek().split(b"\n")[0].split(b"\t"))
    if 1 <= n_fields <= 5:
        return iter_tsv_sentences_official(fileobj)
    elif n_fields == 9:  # at least the example @kercos committed has 9 tabs in the first line
        return iter_tsv_sentences_platinum(fileobj)
    else:
        raise Exception("Bad input file: not a PARSEME TSV format")


def iter_tsv_sentences_official(fileobj):
    # Format: rank|token|nsp|mwe-codes|pos
    sentence = TSVSentence()
    for line in fileobj:
        if line.strip():
            fields = line.strip().split('\t')
            fields.extend([""]*5)  # fill in the optional fields
            surface = fields[1]
            nsp = (fields[2] == 'nsp')
            mwe_codes = [] if fields[3] in EMPTY else fields[3].strip().split(";")
            pos = None if fields[4] in EMPTY else fields[4]
            sentence.append(TSVWord(surface, nsp, mwe_codes, pos))
        else:
            yield sentence
            sentence = TSVSentence()
    if sentence:
        yield sentence


def iter_tsv_sentences_platinum(fileobj):
    # Format: rank|token|nsp|mtw|first-mwe-id|type|second-mwe-id|type
    next(fileobj); next(fileobj)  # skip the 2-line header
    sentence = TSVSentence()
    for line in fileobj:
        if line.strip():
            fields = line.strip().split('\t')
            fields.extend([""]*9)  # fill in the optional fields
            surface = fields[1]
            nsp = (fields[2] == 'nsp')
            # Ignore MTW in fields[3]
            mwe_code_1 = [] if fields[4] in EMPTY else ["{}:{}".format(fields[4], fields[5])]
            mwe_code_2 = [] if fields[6] in EMPTY else ["{}:{}".format(fields[6], fields[7])]
            # Ignore free comments in fields[8]
            sentence.append(TSVWord(surface, nsp, mwe_code_1 + mwe_code_2, None))
        else:
            yield sentence
            sentence = TSVSentence()
    if sentence:
        yield sentence


#####################################################################

if __name__ == "__main__":
    import sys
    with open(sys.argv[1]) as f:
        for tsv_sentence in iter_tsv_sentences(f):
            print("TSVSentence:", tsv_sentence)
            print("MWEs:", tsv_sentence.mwe_infos())

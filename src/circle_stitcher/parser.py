"""Language parser."""

import pyparsing as pp

H_lit = pp.Literal("H")
OC_lit = pp.Literal("OC")
IC_lit = pp.Literal("IC")

K_lit = pp.Literal("K")
N_lit = pp.Literal("N")
M_lit = pp.Literal("M")

L_lit = pp.Literal("L")
S_lit = pp.Literal("S")
C_lit = pp.Literal("C")

integer = pp.Word(pp.nums)
integer.set_parse_action(lambda tokens: int(tokens[0]))

k_option = K_lit + pp.pyparsing_common.fnumber("k")
n_option = N_lit + integer("n")
m_option = M_lit + integer("m")

h_option = H_lit + integer("holes")
outer_circle_option = OC_lit + pp.pyparsing_common.fnumber("outer_circle")
inner_circle_option = IC_lit + pp.pyparsing_common.fnumber("inner_circle")
l_option = L_lit + pp.DelimitedList(integer)("lengths")
s_option = S_lit + integer("start_hole")
c_option = C_lit + integer("chord_count")

statement = l_option + pp.Opt(s_option) + pp.Opt(c_option)
preamble = (
    pp.Opt(h_option)
    + pp.Opt(outer_circle_option)
    + pp.Opt(k_option)
    + pp.Opt(n_option)
    + pp.Opt(m_option)
    + pp.Opt(inner_circle_option)
)

grammar = preamble + pp.Opt(
    pp.DelimitedList(pp.Group(statement), delim=";")("statements")
)


def parse(commands: str) -> pp.ParseResults:
    """Parse Circle Stitcher language string."""
    return grammar.parse_string(commands)

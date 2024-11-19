"""
A list of lines to manually filter out of solutions
"""

MANUAL_LINE_FILTERS = [
    "If there are any mistakes, feel free to edit so that it is correct.",
    "The problems on this page are copyrighted by the Mathematical Association of America's American Mathematics Competitions.",
    "<i>Credit for this solution goes to Ravi Boppana.</i>",
    '"Credit: Skupp3"',  # 1970 AHSME #34
    "Solasky (talk) 12:29, 27 May 2023 (EDT)",  # 1979 AHSME #28
    "Support Me",  # 1980 AHSME #3
    "pi_is_3.141",  # e.g. 1983 AIME #11, 1988 AIME #14
    "-Credit to Adamz for diagram-",  # 1983 AIME #15
    "This is not hard to derive using a basic knowledge of linear transformations. You can refer here for more information: https://en.wikipedia.org/wiki/Orthogonal_matrix",  # 1988 AIME #14
    "-$\\LaTeX$ by Kevinliu08",  # 1989 AHSME #6
    "<b>-Solution by thecmd999</b>",  # 1989 AHSME #19
    "(The original author made a mistake in their solution. Corrected and further explained by dbnl.)",  # 1989 AIME #15
    "_Diagram by 1-1 is 3_",  # 1991 AIME #11
    "JINZHENQIAN",  # 1991 AIME #15
    "Note: The diagram was not given during the actual contest.",  # 1994 AIME #2
    "* Isogonal conjugate",  # 1995 USAMO #3
    # 1996 AIME #9
    "(Note: If you try to do this, first look through all the problems! -Guy)",
    "Edit from EthanSpoon, Doing this with only even numbers will make it faster.",
    "You'll see.",
    "02496",
    "<i>For more detailed explanations, see related problem (AIME I 2007, 10).</i>", # 1997 AIME #8
    "Fixed the link",  # 1999 AHSME #21
    "Solution edited by armang32324 and integralarefun",  # 2000 AMC_12 #2
    "(Note: This Solution is a lot faster if you rule out $(Y, Z) = (1, 7)$ due to degeneracy.)",  # 2000 AIME_II #11
    "By J Steinhardt, from AoPS Community",  # 2000 USAMO #3
    "Problems 8,9 and 10 use the data found in the accompanying paragraph and table:",  # 2002 AMC_8 #8-10
    "Problems 8, 9 and 10 use the data found in the accompanying paragraph and figures",  # 2003 AMC_8 #8-10
    "(NOTE: Variation of other solutions)",  # 2003 AMC_10A #21
    "(JK lol)",  # 2003 AMC_12A #17
    # 2006 AMC_8 #14-16
    "Problems 14, 15 and 16 involve Mrs. Reed's English assignment. ",
    "A Novel Assignment ",
    "For more information, see also  prime factorizations of a factorial.",  # 2006 AIME_II #3
    "Solution by e_power_pi_times_i/edited by srisainandan6",  # 2006 AIME_II #12
    "- (OmicronGamma)",  # 2009 AIME_II #7
    "MegaBoy6679 :D 23:31, 26 December 2022 (EST)",  # 2011 AMC_8 #5
    "Sorry for the sloppy explanation. It's been two years since I've tried to give a solution to a problem, and this is the first time I've really used \\LaTeX. But I think this solution takes a different approach than the one above.",  # 2012 AMC_12A #24
    "--Lightest 15:31, 7 May 2012 (EDT)",  # 2012 USAJMO #3
    "$\\phantom{solution and diagram by bobjoe123}$",  # 2013 AMC_10A #23
    "(Solution by unknown, latex/asy modified majorly by samrocksnature)",  # 2013 AMC_12A #19
    "courtesy v_enhance, minor clarification by integralarefun",  # 2013 USAMO #1
    "Amkan2022",  # 2013 USAJMO #1
    "----MiracleMaths",  # 2014 AMC_8 #14
    "(Lokman G\u00d6K\u00c7E)",  # e.g. 2014 USAMO #5, 2021 AIME_I #6
    "The following solution is due to Gabriel Dospinescu and v_Enhance (also known as Evan Chen).",  # 2014 USAMO #6
    "Note: the original problem did not specify $n>1$, so $n=1$ was a solution, but this was fixed in the Wiki problem text so that the answer would make sense. -- @adihaya (talk) 15:23, 19 February 2016 (EST)",  # 2015 AMC_12B #17
    "This solution was brought to you by Leonard_my_dude.",  # 2015 AIME_II #15
    "- [mathMagicOPS]",  # 2016 AMC_12A #21
    "Non-trig solution by e_power_pi_times_i",  # 2016 AMC_12B #13
    "This solution was brought to you by LEONARD_MY_DUDE",  # 2016 AIME_II #12
    "by: CHECKMATE2021 (edited by CHECKMATE2021)",  # 2017 AMC_8 #7
    "Quality Control by fasterthanlight",  # 2017 AMC_10A #17
    "Credit to Michael Andrejkovics for providing the GeoGebra widget used to make these diagrams!",  # 2017 AMC_12A #17
    "This solution is brought to you by a1b2",  # 2017 AIME_I #13
    "Solution by stephcurry added to the wiki by Thedoge edited by Rapurt9 and phoenixfire",  # 2017 AIME_II #14
    "vvsss</b>   (Reconstruction)",  # 2017 AIME_II #15
    "If you were stuck on this problem, refer to AOPS arithmetic lessons.",  # 2018 AMC_8 #5
    "(helped by qkddud)",  # 2018 AMC_8 #6
    "If you got stuck on this problem, refer to AOPS Number Theory. You're smart.",  # 2018 AMC_8 #7
    "If you got stuck on this problem, refer to AOPS Probability and Combinations",  # 2018 AMC_8 #11
    "Note: Please do not learn Barycentric Coordinates for the AMC 8.",  # 2018 AMC_8 #22
    "Jonathan Xu (pi_is_delicious_69420)",  # 2018 AMC_10B #6
    "<b>Contributors</b>",  # 2018 AMC_12A #10
    "(projecteulerlover)",  # 2018 AMC_12A #16
    "$\\textbf{Note: This is the same problem as 2018 USAJMO Problem 5.}$",  # 2018 USAMO #4
    "(Monday G. Fern)",  # 2018 USAJMO #3
    "(sujaykazi)",  # 2018 USAJMO #4
    "EarthSaver 15:13, 11 June 2021 (EDT)",  # 2019 AMC_8 #13
    "-very small latex edit from countmath1 :)",  # 2019 AMC_10A #24
    "Minor rephrasing for correctness and clarity ~ Technodoggo",  # 2019 AMC_10A #24
    "minor edit (the inclusion of not) by AlcBoy1729",  # 2019 AMC_12B #2
    # 2019 AMC_12B #15
    "Note from ~milquetoast: I found this solution incredibly unspecific and difficult to understand, especially in defining C,  because of the wording. I think what this solution is trying to say is the same as the first video solution down below.",
    "Note from ~<B+: I also believe this solution is worded inefficiently and is not very comprehensible. I hope that someone can make this solution a little bit more understandably good as I'm not very good at explaining things so I cannot. :)",
    "<b>Contributors:</b>",  # 2019 AMC_12B #23
    "<b>- Emathmaster</b>",  # 2019 AIME_I #8
    "- Diagram by Brendanb4321 extended by Duoquinquagintillion",  # 2019 AIME_II #1
    "<b>SpecialBeing2017</b>",  # 2019 AIME_II #13
    "This solution is directly based of @CantonMathGuy's solution.",  # 2019 AIME_II #15
    "Thanks to MRENTHUSIASM for the inspiration!",  # 2020 AMC_8 #1
    "EarthSaver 15:12, 11 June 2021 (EDT)",  # 2020 AMC_8 #1
    "$\\textbf{- Emathmaster}$",  # 2020 AMC_10B #19
    "To see a diagram of $S(r)$, view TheBeautyofMath's explanation video (Video Solution 1).",  # 2020 AMC_10B #20
    "$\\LaTeX$ and formatting adjustments and intermediate steps for clarification by Technodoggo.",  # 2020 AIME_II #10
    "This solution was brought to you by ~Leonard_my_dude~",  # 2021 AIME_I #7
    "<i>~pog</i> ~MathFun1000 (Minor Edits)",  # 2022 AMC_8 #2
    "Edits and Diagram by ~KingRavi and",  # 2022 AMC_10A #10
    "cr. djmathman",  # 2022 AMC_12B #16
    "(NOTE: THE FOLLOWING DIAGRAM WAS NOT SHOWN DURING THE ACTUAL EXAM, BUT IS NOW HERE TO GUIDE STUDENTS IN PICTURING THE PROBLEM)",  # 2023 AMC_8 #15
    "(Note: you could also \"cheese\" this problem by brute force/listing out all of the letters horizontally in a single line and looking at the repeating pattern. Refer to solution 4)",  # 2023 AMC_8 #16
    "Solution by ILoveMath31415926535 and clarification edits by apex304",  # 2023 AMC_8 #22
    "(~edits by KMSONI)",  # 2023 AMC_8 #24
    "(Minor formatting by Technodoggo)",  # 2023 AMC_10A #6
    "(Clarity & formatting edits by Technodoggo)",  # 2023 AMC_12A #9
    "<font size=\"2\">Solution by Quantum-Phantom</font>",  # 2024 AIME_I #13 and #14
    # 2024 AMC_12A #25
    (
        "This problem is the same as problem 7.64 in the Art of Problem Solving textbook "
        "Precalculus chapter 7 that asks to prove $\\tan{nx} = \\frac{\\binom{n}{1}\\tan{x} - "
        "\\binom{n}{3}\\tan^{3}{x} + \\binom{n}{5}\\tan^{5}{x} - \\binom{n}{7}\\tan^{7}{x} + "
        "\\dots}{1 - \\binom{n}{2}\\tan^{2}{x} + \\binom{n}{4}\\tan^{4}{x}  - "
        "\\binom{n}{6}\\tan^{6}{x} + \\dots}$"
    ),
    # for 2023 AMC_10B #9
    "A very similar solution offered by ~darrenn.cp and ~DarkPheonix has been combined with Solution 1.",
    "Minor corrections by",
    "Note from ~milquetoast: Alternatively, you can let $x$ be the square root of the larger number, but if you do that, keep in mind that $x=1$ must be rejected, since $(x-1)$ cannot be $0$.",

    # Various incomplete olympiad solutions
    "[WIP]",  # 2022 USAMO #3
    "Coming soon.",  # 2022 USAMO #5
    "No Solution Here Yet!",  # 2022 USAMO #6
    "<i>This problem needs a solution. If you have a solution for it, please help us out by <span class=\"plainlinks\">adding it</span>.</i>",  # e.g. 2020 USAMO #5
]

ASY_COMMON_RE = r"//\s*([Cc]redit|[Mm]ade|[Dd]iagram|[Cc]reated|[Cc]hanges made) (by|to) \w+( and \w+)?"
ASY_DOUBLE_SLASH_CREDIT_COMMENTS = [
    "// pog diagram ",
    "// Credits given to Themathguyd\u200e and Kante314 ",
    r"//(Diagram Creds-DivideBy0)\s*",
    "// Asymptote by Technodoggo; August 16, 2024 ",
    "//Made by Afly. I used some resources. //Took me 10 min to get everything right. ",
    "// TheMathGuyd ",
    "// Diagram by TheMathGuyd. I can compress this later ",
    "// Diagram by TheMathGuyd. I can compress this later ",
    "// Diagram by TheMathGuyd. Found cubic, so graph is perfect. ",
    r"// Diagram by TheMathGuyd. I even put the lined texture :\) ",
    r"//Restored original diagram. Alter it if you would like, but it was made by TheMathGuyd, I even put the lined texture :\) "
    "// Thank you Kante314 for inspiring thicker arrows. They do look much better "
    rf"{ASY_COMMON_RE} give me 1 billion dollars for this\.?\s*",
    rf"{ASY_COMMON_RE} for the asymptote\.?\s*",
    rf"{ASY_COMMON_RE} for the diagram\.?\s*",
    rf"{ASY_COMMON_RE}(,| and) edited by \w+\.?\s*",
    rf"{ASY_COMMON_RE}\.?\s*",
]

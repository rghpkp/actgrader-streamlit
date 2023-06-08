# st_ACT_202006.py

# Writes the blank 201906 ACT scoring table as a python dict.
# Run file in a session to load the scoring table in a namespace.
#
# exec( open('st_ACT_123456.py').read() )
#

scoring_table = {
    'test_code':'202006',
    'table':{
        1:{'e':range(0,2), 'm':range(0,1), 'r':range(0,1), 's':range(0,1)},
        2:{'e':range(2,4), 'm':range(0,0), 'r':range(1,2), 's':range(0,0)},
        3:{'e':range(4,5), 'm':range(0,0), 'r':range(0,0), 's':range(1,2)},
        4:{'e':range(5,7), 'm':range(1,2), 'r':range(2,3), 's':range(2,3)},
        5:{'e':range(7,9), 'm':range(0,0,), 'r':range(3,4), 's':range(0,0)},
        6:{'e':range(9,10), 'm':range(2,3), 'r':range(4,5), 's':range(3,4)},
        7:{'e':range(11,13), 'm':range(0,0), 'r':range(0,0), 's':range(4,5)},
        8:{'e':range(14,15), 'm':range(3,4), 'r':range(5,6), 's':range(5,6)},
        9:{'e':range(15,18), 'm':range(0,0), 'r':range(6,7), 's':range(6,7)},
        10:{'e':range(18,21), 'm':range(4,5), 'r':range(7,9), 's':range(7,8)},
        11:{'e':range(21,24), 'm':range(5,6), 'r':range(9,10), 's':range(8,10)},
        12:{'e':range(24,26), 'm':range(6,8), 'r':range(10,12), 's':range(10,11)},
        13:{'e':range(26,28), 'm':range(8,10), 'r':range(12,13), 's':range(11,12)},
        14:{'e':range(28,31), 'm':range(10,13), 'r':range(13,14), 's':range(12,13)},
        15:{'e':range(31,35), 'm':range(13,17), 'r':range(14,16), 's':range(13,15)},
        16:{'e':range(35,38), 'm':range(17,20), 'r':range(16,17), 's':range(15,17)},
        17:{'e':range(38,40), 'm':range(20,23), 'r':range(17,18), 's':range(17,18)},
        18:{'e':range(40,42), 'm':range(23,26), 'r':range(18,20), 's':range(18,20)},
        19:{'e':range(42,44), 'm':range(26,28), 'r':range(20,21), 's':range(20,21)},
        20:{'e':range(44,47), 'm':range(28,29), 'r':range(21,22), 's':range(21,23)},
        21:{'e':range(47,49), 'm':range(29,31), 'r':range(22,24), 's':range(23,24)},
        22:{'e':range(49,52), 'm':range(31,32), 'r':range(24,25), 's':range(24,26)},
        23:{'e':range(52,55), 'm':range(32,34), 'r':range(25,27), 's':range(26,27)},
        24:{'e':range(55,58), 'm':range(34,36), 'r':range(27,28), 's':range(27,29)},
        25:{'e':range(58,60), 'm':range(36,39), 'r':range(28,29), 's':range(29,30)},
        26:{'e':range(60,62), 'm':range(39,41), 'r':range(29,30), 's':range(30,31)},
        27:{'e':range(62,63), 'm':range(41,44), 'r':range(30,31), 's':range(31,33)},
        28:{'e':range(63,65), 'm':range(44,47), 'r':range(31,32), 's':range(0,0)},
        29:{'e':range(65,66), 'm':range(47,49), 'r':range(32,33), 's':range(33,34)},
        30:{'e':range(66,67), 'm':range(49,51), 'r':range(33,34), 's':range(34,35)},
        31:{'e':range(67,68), 'm':range(51,53), 'r':range(34,35), 's':range(35,36)},
        32:{'e':range(68,69), 'm':range(53,54), 'r':range(35,36), 's':range(36,37)},
        33:{'e':range(69,71), 'm':range(54,55), 'r':range(36,37), 's':range(0,0)},
        34:{'e':range(71,72), 'm':range(55,57), 'r':range(37,38), 's':range(37,38)},
        35:{'e':range(72,74), 'm':range(57,59), 'r':range(38,40), 's':range(38,39)},
        36:{'e':range(74,76), 'm':range(59,61), 'r':range(40,41), 's':range(39,41)}
    }
}

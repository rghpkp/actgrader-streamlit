# st_ACT_202112.py

# The blank {tc} ACT scoring table as a python dict. After filling
# in the ranges, run the file in a session to load the scoring table
# in a namespace:

# exec( open('st_ACT_123456.py').read() )
#


scoring_table = {
    'test_code':202112,
    'table':{
        1:{'e':range(0,2), 'm':range(0,1), 'r':range(0,1), 's':range(0,1)},
        2:{'e':range(2,3), 'm':range(0,0), 'r':range(1,2), 's':range(0,0)},
        3:{'e':range(3,5), 'm':range(0,0), 'r':range(0,0), 's':range(1,2)},
        4:{'e':range(5,6), 'm':range(0,0), 'r':range(2,3), 's':range(2,3)},
        5:{'e':range(6,8), 'm':range(1,2), 'r':range(3,4), 's':range(0,0)},
        6:{'e':range(8,10), 'm':range(0,0), 'r':range(0,0), 's':range(3,4)},
        7:{'e':range(10,12), 'm':range(2,3), 'r':range(4,5), 's':range(4,5)},
        8:{'e':range(12,14), 'm':range(0,0), 'r':range(5,6), 's':range(5,6)},
        9:{'e':range(14,16), 'm':range(3,4), 'r':range(6,7), 's':range(6,7)},
        10:{'e':range(16,19), 'm':range(4,5), 'r':range(7,8), 's':range(7,8)},
        11:{'e':range(19,23), 'm':range(5,6), 'r':range(8,9), 's':range(8,9)},
        12:{'e':range(23,25), 'm':range(6,7), 'r':range(9,11), 's':range(9,10)},
        13:{'e':range(25,26), 'm':range(7,9), 'r':range(11,13), 's':range(10,11)},
        14:{'e':range(26,28), 'm':range(9,12), 'r':range(13,14), 's':range(11,12)},
        15:{'e':range(28,32), 'm':range(12,15), 'r':range(14,16), 's':range(12,13)},
        16:{'e':range(32,34), 'm':range(15,19), 'r':range(16,17), 's':range(13,15)},
        17:{'e':range(34,36), 'm':range(19,22), 'r':range(17,19), 's':range(15,16)},
        18:{'e':range(36,38), 'm':range(22,25), 'r':range(19,20), 's':range(16,18)},
        19:{'e':range(38,40), 'm':range(25,27), 'r':range(20,21), 's':range(18,19)},
        20:{'e':range(40,43), 'm':range(27,29), 'r':range(21,23), 's':range(19,21)},
        21:{'e':range(43,46), 'm':range(29,30), 'r':range(23,24), 's':range(21,22)},
        22:{'e':range(46,49), 'm':range(30,32), 'r':range(24,26), 's':range(22,24)},
        23:{'e':range(49,52), 'm':range(32,35), 'r':range(26,27), 's':range(24,26)},
        24:{'e':range(52,55), 'm':range(35,37), 'r':range(27,29), 's':range(26,28)},
        25:{'e':range(55,57), 'm':range(37,39), 'r':range(29,30), 's':range(28,30)},
        26:{'e':range(57,59), 'm':range(39,42), 'r':range(0,0), 's':range(30,32)},
        27:{'e':range(59,60), 'm':range(42,45), 'r':range(30,31), 's':range(32,33)},
        28:{'e':range(60,62), 'm':range(45,47), 'r':range(31,32), 's':range(33,34)},
        29:{'e':range(62,63), 'm':range(47,49), 'r':range(32,33), 's':range(0,0)},
        30:{'e':range(63,65), 'm':range(49,51), 'r':range(33,34), 's':range(34,35)},
        31:{'e':range(65,66), 'm':range(51,53), 'r':range(34,35), 's':range(35,36)},
        32:{'e':range(66,67), 'm':range(53,54), 'r':range(35,36), 's':range(36,37)},
        33:{'e':range(67,68), 'm':range(54,55), 'r':range(36,37), 's':range(37,38)},
        34:{'e':range(68,70), 'm':range(55,57), 'r':range(37,38), 's':range(0,0)},
        35:{'e':range(70,73), 'm':range(57,59), 'r':range(38,39), 's':range(38,39)},
        36:{'e':range(73,76), 'm':range(59,61), 'r':range(39,41), 's':range(39,41)}
    }
}

import os

import mdata
import utils

if __name__ == "__main__":
    # example file path 
    path = r'C:\test_mdata_file.txt'

    # mdata generation
    test_mdata = mdata.MData(fpath=path)
    # adding some tags to the file
    test_mdata.add_tags("user", "text", "important")

    # debug prints
    print(test_mdata)
    print(test_mdata.c_time)
    print(test_mdata.m_time)
    print(test_mdata.size)
    print(test_mdata.creation_time)
    print(test_mdata.last_edit_time)
    print(test_mdata.get_file_size(unit=utils.FILESIZE.KILOBYTE))

    # serialize test_mdata and create a new copy
    test_mdata.save()
    json_data = test_mdata.serialize()
    test_mdata_2 = mdata.MData(fpath=path, data=json_data)

    # tag manipulation
    test_mdata_2.remove_tags("important")

    # example of tag query
    print(test_mdata.filter(utils.FILTERMODE.ANY, "text", "wrong_tag")) #True
    print(test_mdata.filter(utils.FILTERMODE.ALL, "text", "wrong_tag")) #False

    # example of getting a non-existent value from an enum
    print(utils.FILTERMODE.get_name(43))
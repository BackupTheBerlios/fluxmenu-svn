'''Written by Michael Rice
Copyright Nov 14, 2005
Released under the terms of the GNU GPL v2
Email: Michael Rice errr@errr-online.com
Website: http://errr-online.com/
'''
import os,re

def parse_file(file):
    """read config file place results into a 
    dict file location provided by caller. 
    keys = options (USEICONS, ICONPATHS, etc)
    values = values from options
    config file should be in the form of:
    OPTION:values:moreValuse:evenMore
    do not end with ":"  Comments are "#" as 
    the first char.
    #OPTION:commet
    OPTION:notComment #this is not valid comment
    """

    opts = {}
    if os.path.isfile(file):
        match = re.compile(r"^[^#^\n]")
        f = open(file)
        info = f.readlines()
        f.close()
        keys = []
        for lines in info:
            if match.findall(lines):
                keys.append( lines.strip().split(":") )

        for i in range(len(keys)):
            opts[keys[i][0]] = keys[i][1:]
        return opts    

    else:
        return None


def save_config(file, config):
    """save config to 'file', 'config' should
    be a dict, in this format:
    { key: [value1, value2] }
    So values are a table.

    Config will always be overwritten if
    it is not write protected.

    Returns 1 on success, 0 on error"""

    cFile = open(file, "w")

    if not cFile: return 0

    for item in config:
        line = item.strip()

        for value in config[item]:
            line = line + ':' + str(value).strip()

        line = line + '\r\n'

        cFile.write(line)


    cFile.close()

    return 1



if __name__ == "__main__":
    conf = parse_file("/home/zan/Projects/fluxmenu/testConfig")
    print conf
    save_config("/home/zan/Projects/fluxmenu/testConfig2", conf)

##***********************************************************************
## 
## Project	: MDCS
## Filename	: check_param_consistency.py
## Date         : 13/05/2016
## Author	: Duminda	
## Purpose	: This script contains multiple functions to carry out param related tasks with.
##                The initial half of the code provides a way to define parameter formats. The next half deals with specific tasks using the earlier framework.


from struct import pack, unpack
import os
from zlib import crc32
import sys, getopt
import subprocess
import shutil
import time
from random import randint
import filecmp
import logging
from datetime import datetime

pack_lengths = dict(c=1, b=1, B=1, h=2, H=2, i=4, I=4, l=4, L=4)
endianness = '>'

def get_pack_length(pack_format):
    v = pack_lengths.get(pack_format)
    if v != None:
        return v
    #only check for strings otherwise.
    i = pack_format.find('s')
    if i == -1:
        raise Exception('Unknown pack_format', pack_format)
    return int(pack_format.split('s')[0])

def get_endian_corrected_pack_format(pack_format):
    return endianness + pack_format

g_offset = 0

class data_type:
    def __init__(self, pack_format, read_as_string=False, bit_size=0):
        self.pack_format = pack_format
        self.length = get_pack_length(pack_format)
        self.is_string = False
        self.bit_size = bit_size
        self.read_as_string = read_as_string
        if pack_format.find('s') != -1:
            self.is_string = True

    def read(self, fd):
        barr = fd.read(self.length)
        global g_offset
        g_offset = g_offset + self.length
        res = unpack(get_endian_corrected_pack_format(self.pack_format), barr)
        ret = res[0]
        if self.is_string == True and self.read_as_string == True:
            ret = res[0].split(b'\0', 1)[0].decode("ascii")
        elif self.bit_size > 0:
            ret = ret & ((2**self.bit_size) - 1)
        return ret

    def write(self, fd, value):
        res = None
        if self.is_string == True:
            if self.read_as_string == True:
                res = pack(get_endian_corrected_pack_format(self.pack_format), value.encode('ascii'))
            else:
                res = pack(get_endian_corrected_pack_format(self.pack_format), value)
        else:
            if self.bit_size == 0:
                res = pack(get_endian_corrected_pack_format(self.pack_format), value)
            else:
                res = pack(get_endian_corrected_pack_format(self.pack_format), value & ((2**self.bit_size) - 1))
        fd.write(res)

#########Predef data types############

dt_byte = data_type('b')
dt_us_byte = data_type('B')
dt_short = data_type('h')
dt_us_short = data_type('H')
dt_int = data_type('i')
dt_us_int = data_type('I')
dt_long = data_type('l')
dt_us_long = data_type('L')

######################################

##I could have sub-classed this. (i.e. element, field_element, composite_element, run_element). But this is what we are stuck with now.
class element:
    def __init__(self, definition, value = []):
        self.definition = definition
        self.value = value
        self.offset = 0

    def describe(self):
        return self.definition.describe

    def output(self, currenttab = '', tab = '  '):
        return self.definition.output(self, currenttab, tab)

    def write(self, fd):
        self.definition.write(fd, self)

    def map_over(self, function):
        self.definition.map_over(function, self)        

#####################################

class element_def:
    def __init__(self, name):
        self.name = name
        self.parent = None

    def read(self, fd, element):
        pass

    def write(self, fd):
        pass

    def describe(self):
        pass

    def set_parent(self, parent):
        self.parent = parent

    def on_read(self, child, elem):
        pass

    def output(self, element):
        pass

    def get_child(self, name):
        pass

    #Flesh out.
    def map_over(self, function, elem):
        pass

    def create_element(self, value):
        pass

class field_def(element_def):
    def __init__(self, name, data_type):
        super(field_def, self).__init__(name)
        self.data_type = data_type

    def read(self, fd):       
        f = element(self)

        global g_offset
        f.offset = g_offset
        
        res = self.data_type.read(fd)
        f.value = res

        if self.parent != None:
            self.parent.on_read(self, f)
        
        return f

    def write(self, fd, elem):
        self.data_type.write(fd, elem.value)

    def describe(self):
        return 'field def : {} '.format(self.name)

    def output(self, element, currenttab, tab):
        return '{}{} = {}'.format(currenttab, self.name, element.value)

    def map_over(self, function, elem):
        function(self.name, self, elem.value)

    def get_child(self, name):
        return None

    def create_element(self):
        return element(self, None)

class composite_def(element_def):
    def __init__(self, name, defs):
        super(composite_def, self).__init__(name)
        self.defs = defs
        self.setters = dict()

    def read(self, fd):        
        c = element(self)
        
        global g_offset
        c.offset = g_offset
        
        res = [e.read(fd) for e in self.defs]
        c.value = res

        if self.parent != None:
            self.parent.on_read(self, c)
        
        return c

    def write(self, fd, elem):
        for v in elem.value:
            v.write(fd)

    def describe(self):
        s = '\n' + ''.join([e.describe().replace('\n', '\n\t') + '\n' for e in selfroot_elem.defs])
        return 'composite def : {}'.format(self.name) + s

    def set_parent(self, parent):
        self.parent = parent
        for e in self.defs:
            e.set_parent(self)

    def map_count(self, count_obj):
        count_obj.register(self.setters)

    def on_read(self, child, element):
        v = self.setters.get(child.name)
        if v == None:
            return
        v.set_count(element.value)

    def output(self, element, currenttab, tab):
        s = '\n' + ''.join([e.output(currenttab + tab, tab) + '\n' for e in element.value])
        return '{}{} = {}'.format(currenttab, self.name, s[:len(s) - 1])

    def map_over(self, function, elem):
        function(self.name, self, elem.value)
        for e in elem.value:
            e.map_over(function)

    def get_child(self, name):
        return [d for d in self.defs if d.name == name][0]

    def create_element(self):
        return element(self, [d.create_element() for d in self.defs])

class fixed_count:
    def __init__(self, count):
        self.count = count

    def set_count(self, count):
        pass

    def register(self, hook_map):
        pass

class named_count:
    def __init__(self, count_name):
        self.count_name = count_name
        self.count = 0

    def set_count(self, count):
        self.count = count

    def register(self, hook_map):
        hook_map[self.count_name] = self

class element_run_def(element_def):
    def __init__(self, name, run_def, count_obj, sort_field = None):
        super(element_run_def, self).__init__(name)
        self.run_def = run_def
        self.count_obj = count_obj
        self.sort_field = sort_field

    def read(self, fd):        
        c = element(self)
        
        global g_offset
        c.offset = g_offset
        
        ret = []
        for i in range(0, self.count_obj.count):
            ret.append(self.run_def.read(fd))
        c.value = ret
        
        if self.parent != None:
            self.parent.on_read(self, c)
        return c

    def write(self, fd, elem):
        for v in elem.value:
            v.write(fd)

    def output(self, element, currenttab, tab):
        s = '\n' + ''.join([e.output(currenttab + tab, tab) + '\n' for e in element.value])
        return '{}{} = {}'.format(currenttab, self.name, s)

    def set_parent(self, parent):
        self.parent = parent
        self.parent.map_count(self.count_obj)
        self.run_def.set_parent(self)

    def map_over(self, function, elem):
        function(self.name, self, elem.value)
        for e in elem.value:
            e.map_over(function)

    def get_child(self, name):
        return [d for d in self.run_def.defs if d.name == name][0]

    def create_element(self):
        return element(self, [])

    def sort_values(self, values):
        if self.sort_field == None:
            return
        values.sort(key = lambda x: get_child_element(x, self.sort_field).value)

#Header format. Common to all params.
param_header = composite_def('header',
                            [field_def('file_id', dt_us_short),
                            field_def('format_version', dt_us_byte),
                            field_def('param_version', dt_short),
                            field_def('length', dt_us_long),
                            field_def('eff_datetime', dt_long),
                            field_def('location_id', dt_us_short),
                            field_def('unused', dt_us_byte)])

def define_param(name, defs):
    d = [param_header]
    d.extend(defs)
    ret = composite_def(name, d)
    ret.set_parent(None)
    return ret

def read_param(filename, definition):
    global g_offset
    g_offset = 0
    
    fd = open(filename, 'r+b')
    ret = definition.read(fd)
    fd.close()
    return ret

def write_length_and_crc(path):
    fd = open(path, 'r+b')
    b = fd.read()
    calc_crc = crc32(b)
    barr = pack('>L', calc_crc)
    fd.write(barr)
    fd.close()

    length = os.path.getsize(path)

    h = read_param(path, param_header)
    get_child_element(h, "length").value = length
    overwrite_param(path, h)

def rewrite_crc(path):
    fd = open(path, 'r+b')
    length = os.path.getsize(path)
    b = fd.read(length - 4)
    calc_crc = crc32(b)
    barr = pack('>L', calc_crc)
    fd.seek(length-4)
    fd.write(barr)
    fd.close()

def write_param(filename, elem):
    fd = open(filename, 'w+b')
    elem.write(fd)
    fd.close()
    
    write_length_and_crc(filename)

def overwrite_param(filename, elem):
    fd = open(filename, 'r+b')

    fd.seek(elem.offset)
    elem.write(fd)
    fd.close()

    rewrite_crc(filename)

def get_child_element(element, name):
    return [x for x in element.value if x.definition.name == name][0]

def create_empty_element(param, header):
    elem = param.create_element()
    h = get_child_element(elem, 'header')
    h.value = header
    return elem
    
########################### Some concrete param formats. #################################

mdcsmbl = define_param('mdcsmbl',
                        [field_def('num_buses', dt_us_int),
                         element_run_def('buses',
                                        composite_def('bus_entry',
                                                        [field_def('bus_number', data_type('8s', True)),
                                                        field_def('sp_id', dt_us_byte),
                                                        field_def('effective_date', dt_int),
                                                        field_def('depot_bitmap', data_type('25s'))]),
                                            named_count('num_buses'), 'bus_number')])

mdcstdl = define_param('mdcstdl',
                        [field_def('num_buses', dt_us_int),
                         element_run_def('buses',
                                        composite_def('bus_entry',
                                                        [field_def('bus_number', data_type('8s', True)),
                                                        field_def('group_bitmap', data_type('B', False, 3))]),
                                            named_count('num_buses'), 'bus_number')])

sep_pdt = define_param('sep_pdt',
                       [field_def('num_files', dt_us_byte),
                        element_run_def('files',
                                        composite_def('file',
                                                      [field_def('file_id', dt_us_short),
                                                       field_def('file_name', data_type('12s', True)),
                                                       field_def('param_version', dt_us_short),
                                                       field_def('location_path', data_type('32s', True))]),
                                        named_count('num_files'),
                                        'file_name')])

gcm_pdt = define_param('gcm_pdt',
                           [field_def('num_files', dt_us_short),
                            element_run_def('files',
                                            composite_def('file',
                                                          [field_def('sp_id', dt_us_byte),
                                                           field_def('depot_id', dt_us_short),
                                                           field_def('file_id', dt_us_short),
                                                           field_def('file_name', data_type('12s', True)),
                                                           field_def('param_version', dt_us_short),
                                                           field_def('location_path', data_type('32s', True))]),
                                            named_count('num_files'),
                                            'file_name')])

dcs_flt = define_param('dcs_flt',
                       [field_def('num_entries', dt_us_short),
                        element_run_def('entries',
                                        composite_def('entry',
                                                      [field_def('bus_number', data_type('8s', True)),
                                                       field_def('bus_group', dt_us_byte),
                                                       field_def('bus_type', dt_us_byte)]),
                                        named_count('num_entries'),
                                        'bus_number')])

################################################################################

def get_folders(path):
    return [[f, os.path.join(dp, f)] for dp,dn,filenames in os.walk(path) for f in dn]

def get_files(path):
    return [[f, os.path.join(dp, f)] for dp,dn,filenames in os.walk(path) for f in filenames]

def get_lvl1_folders(path):
    return [[d, os.path.join(path, d)] for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]

def get_lvl1_files(path):
    return [[d, os.path.join(path, d)] for d in os.listdir(path) if os.path.isfile(os.path.join(path, d))]

def create_header_element(file_id, format_version, param_version, length, eff_datetime, location_id):
    ret = element(param_header)
    ret.value = []
    ret.value.append(element(param_header.get_child('file_id'), file_id))
    ret.value.append(element(param_header.get_child('format_version'), format_version))
    ret.value.append(element(param_header.get_child('param_version'), param_version))
    ret.value.append(element(param_header.get_child('length'), length))
    ret.value.append(element(param_header.get_child('eff_datetime'), eff_datetime))
    ret.value.append(element(param_header.get_child('location_id'), location_id))
    ret.value.append(element(param_header.get_child('unused'), 0))
    return ret

#Feel these create_xxx functions are not needed. Ask the def to create the default element and compose them.

def create_empty_sep_pdt(header_elem):
    root_elem = element(sep_pdt, [])
    num_files_def = sep_pdt.get_child('num_files')
    num_files_elem = element(num_files_def, 0)
    files_def = sep_pdt.get_child('files')
    files_elem = element(files_def, [])
    root_elem.value = [header_elem, num_files_elem, files_elem]
    return root_elem

def create_empty_dcs_flt(header_elem):
    root_elem = element(dcs_flt, [])
    num_entries_def = dcs_flt.get_child('num_entries')
    num_entries_elem = element(num_entries_def, 0)
    entries_def = dcs_flt.get_child('entries')
    entries_elem = element(entries_def, [])
    root_elem.value = [header_elem, num_entries_elem, entries_elem]
    return root_elem

def create_empty_gcm_pdt(header_elem):
    root_elem = element(gcm_pdt, [])
    num_files_def = gcm_pdt.get_child('num_files')
    num_files_elem = element(num_files_def, 0)
    files_def = gcm_pdt.get_child('files')
    files_elem = element(files_def, [])
    root_elem.value = [header_elem, num_files_elem, files_elem]
    return root_elem

def add_to_sep_pdt(root_element, file_id, file_name, param_version, location_path):
    num_files_elem = get_child_element(root_element, 'num_files')
    num_files_elem.value = num_files_elem.value + 1
    files_def = sep_pdt.get_child('files')
    files_elem = get_child_element(root_element, 'files')
    composite_def = files_def.run_def
    composite_elem = element(composite_def, [])
    file_id_def = composite_def.get_child('file_id')
    file_name_def = composite_def.get_child('file_name')
    param_version_def = composite_def.get_child('param_version')
    location_path_def = composite_def.get_child('location_path')

    file_id_elem = element(file_id_def, file_id)
    file_name_elem = element(file_name_def, file_name)
    param_version_elem = element(param_version_def, param_version)
    location_path_elem = element(location_path_def, location_path)

    composite_elem.value = [file_id_elem, file_name_elem, param_version_elem, location_path_elem]
    files_elem.value.append(composite_elem)
    files_def.sort_values(files_elem.value)

def add_to_gcm_pdt(root_element, sp_id, depot_id, file_id, file_name, param_version, location_path):
    num_files_elem = get_child_element(root_element, 'num_files')
    num_files_elem.value = num_files_elem.value + 1
    files_def = gcm_pdt.get_child('files')
    files_elem = get_child_element(root_element, 'files')
    composite_def = files_def.run_def
    composite_elem = element(composite_def, [])
    
    sp_id_def = composite_def.get_child('sp_id')
    depot_id_def = composite_def.get_child('depot_id')
    file_id_def = composite_def.get_child('file_id')
    file_name_def = composite_def.get_child('file_name')
    param_version_def = composite_def.get_child('param_version')
    location_path_def = composite_def.get_child('location_path')

    sp_id_elem = element(sp_id_def, sp_id)
    depot_id_elem = element(depot_id_def, depot_id)
    file_id_elem = element(file_id_def, file_id)
    file_name_elem = element(file_name_def, file_name)
    param_version_elem = element(param_version_def, param_version)
    location_path_elem = element(location_path_def, location_path)

    composite_elem.value = [sp_id_elem, depot_id_elem, file_id_elem, file_name_elem, param_version_elem, location_path_elem]
    files_elem.value.append(composite_elem)
    files_def.sort_values(files_elem.value)

depot_mapping = {'0950' : 'DSL', '0951' : 'DHG', '0952' : 'DSA', '0953' : 'DAR', '0954' : 'DBN', '0955' : 'DBD', '0956' : 'DBB', '0963' : 'DBL'}
        
def add_sys_folder(outgoing_path, root_element, path_prefix):
    sys_folder = [t[1] for t in get_folders(outgoing_path) if t[0] == 'sys'][0]
    sys_files = [t for t in get_files(sys_folder)]

    for t in sys_files:
        filename = t[0]
        path = t[1]
        header = read_param(path, param_header)
        file_id = get_child_element(header, 'file_id').value
        param_version = get_child_element(header, 'param_version').value
        add_to_sep_pdt(root_element, file_id, filename, param_version, path_prefix + path.split(outgoing_path)[1].replace('\\', '/').split('/')[1])

def create_bo_pdts(outgoing_path, path_prefix):
    depot_folders = [t for t in get_folders(outgoing_path) if t[0] != 'sys']

    for depot_folder in depot_folders:
        file_version = 1
        format_version = 1
        file_path = depot_folder[1] + "\\SeP_PDTA." + depot_mapping[depot_folder[0]]
        if os.path.exists(file_path):
            param = read_param(file_path, param_header)
            file_version = get_child_element(param, 'param_version').value
            file_version = file_version + 1
            format_version = get_child_element(param, 'format_version').value
        
        header = create_header_element(0x7364, format_version, file_version, 10000, 1456533722, int(depot_folder[0]))
        root_element = None
        root_element = create_empty_sep_pdt(header)
        
        files = [t for t in get_files(depot_folder[1]) if not t[0].startswith('SeP_PDTA')]
        for t in files:
            filename = t[0]
            path = t[1]
            header = read_param(path, param_header)
            file_id = get_child_element(header, 'file_id').value
            param_version = get_child_element(header, 'param_version').value
            add_to_sep_pdt(root_element, file_id, filename, param_version, path_prefix + path.split(outgoing_path)[1].replace('\\', '/').split('/')[1])

        add_sys_folder(outgoing_path, root_element, path_prefix)

        #print(depot_folder[0])
        write_param(file_path, root_element)

def create_mdcs_sep_pdt(outgoing_folder, depot_path):
    depot_id = depot_path.split('/')[1]
    file_version = 1
    format_version = 2
    pdt_path = os.path.join(outgoing_folder, depot_path, 'SeP_PDTA.SYS')
    if os.path.exists(pdt_path):
        param = read_param(pdt_path, param_header)
        file_version = get_child_element(param, 'param_version').value
        file_version = file_version + 1
        format_version = get_child_element(param, 'format_version').value
    header = create_header_element(0x7364, format_version, file_version, 10000, 1456533722, int(depot_id))

    root_element = None
    root_element = create_empty_sep_pdt(header)

    sub_folders = ['Live', 'Trial']

    for sub in sub_folders:
        sub_path = os.path.join(outgoing_folder, depot_path, sub)
        files = [f for f in get_files(sub_path) if f[0].endswith('SYS') or f[0].startswith('MDCSTDLA')]

        for t in files:
            filename = t[0]
            path = t[1]
            h = read_param(path, param_header)
            file_id = get_child_element(h, 'file_id').value
            param_version = get_child_element(h, 'param_version').value
            add_to_sep_pdt(root_element, file_id, filename, param_version, '/' + depot_path + '/' + sub)

    #print(root_element.output())
    write_param(pdt_path, root_element)
    return file_version

def create_mdcs_pdts(outgoing_path):
    file_version = 1
    format_version = 1
    gcm_pdt_path = os.path.join(outgoing_path, 'GCM_PDTA.SYS')
    if os.path.exists(gcm_pdt_path):
        h = read_param(gcm_pdt_path, param_header)
        file_version = get_child_element(h, 'param_version').value
        file_version = file_version + 1
        format_version = get_child_element(h, 'format_version').value
    header = create_header_element(0x738B, format_version, file_version, 10000, 1456533722, 0)      #length seems to not matter.
    
    new_pdt = create_empty_gcm_pdt(header)

    mdcsmbl_path = os.path.join(outgoing_path, 'MDCSMBLA.SYS')
    if os.path.exists(mdcsmbl_path):
        h = read_param(mdcsmbl_path, param_header)
        file_id = get_child_element(h, 'file_id').value
        param_version = get_child_element(h, 'param_version').value
        add_to_gcm_pdt(new_pdt, 0, 0, file_id, 'MDCSMBLA.SYS', param_version, '')
    
    folders = get_lvl1_folders(outgoing_path)
    for t in folders:
        spid = t[0]
        for u in get_lvl1_folders(t[1]):
            depotid = u[0]
            sp_param_version = create_mdcs_sep_pdt(outgoing_path, spid + '/' + depotid)
            add_to_gcm_pdt(new_pdt, int(spid), int(depotid), 0x7364, 'SeP_PDTA.SYS', sp_param_version, '/{}/{}'.format(spid, depotid))

    write_param(gcm_pdt_path, new_pdt)

def increment_mbl_pdt(outgoing_path):
    mbl_path = os.path.join(outgoing_path, "MDCSMBLA.SYS")
    mbl = read_param(mbl_path, mdcsmbl)
    #print(mbl.output())
    h = get_child_element(mbl, 'header')
    file_ver = get_child_element(h, 'param_version')
    file_ver.value = file_ver.value + 1
    
    write_param(mbl_path, mbl)

    create_mdcs_pdts(outgoing_path)

def increment_file_version(filename):
    h = read_param(filename, param_header)
    pve = get_child_element(h, "param_version")
    pve.value = pve.value + 1

    overwrite_param(filename, pve)

##Increments versions of files in MDCS folder tree, generates new GCM_PDT and SEP_PDTs, pushes generated GCM_PDT down to gateway incoming path.
def increment_version_gun(mdcs_outgoing_path, dagw_incoming_path):
    try:    
        sp_folders = get_lvl1_folders(mdcs_outgoing_path)
        for t in sp_folders:
            spid = t[0]
            for u in get_lvl1_folders(t[1]):
                depotid = u[0]
                for mode_f in ["Live", "Trial"]:
                    for v in get_lvl1_files(os.path.join(u[1], mode_f)):
                        filename = v[1]
                        print("Incrementing file {} version.".format(filename))
                        if not v[0] == "DAGWAPPA.SYS":
                            increment_file_version(filename)

        create_mdcs_pdts(mdcs_outgoing_path)
        gcm_path = os.path.join(mdcs_outgoing_path, "GCM_PDTA.SYS")
        shutil.copy2(gcm_path, dagw_incoming_path)
##    except IOError as ie:
##        logging.exception(ie)
    except Exception as e:
        logging.exception(e)

non_trialable_params = ["BUS_BATA.SYS", "DCS_BLPA", "DCS_BLRA", "DCS_BLSA", "DCS_BLWA", "DCS_CFG?.SYS", "DCS_FLTA.SYS", "GCM_PDTA.SYS", "DAGWAPPA.SYS",
                        "MDCSMBLA.SYS", "MDCSTDLA", "SeP_BUTA.SYS", "SeP_BW1A.SYS", "SeP_DBBA.SYS", "SeP_FBBA.SYS", "SeP_PDTA", "SeP_PDTA.SYS"]

def is_trialable(param_name):
    for param in non_trialable_params:
        if param_name.startswith(param):
            return False
    return True

##-------------------------------------------------------------------------------------------------##
def reset_mdcs_params(mdcs_outgoing_path):
    gcm_pdt_path = os.path.join(mdcs_outgoing_path, "GCM_PDTA.SYS")
    os.remove(gcm_pdt_path)
    
    sp_folders = get_lvl1_folders(mdcs_outgoing_path)
    for t in sp_folders:
        for u in get_lvl1_folders(t[1]):
            depotid = u[0]
            depotpath = u[1]

            sep_pdt_path = os.path.join(depotpath, "SEP_PDTA.SYS")
            os.remove(sep_pdt_path)
            
            params = []
            modes = ["Live", "Trial"]
            for mode_f in modes:
                for v in get_lvl1_files(os.path.join(u[1], mode_f)):
                    filename = v[0]
                    filepath = v[1]

                    h = read_param(filepath, param_header)
                    get_child_element(h, "param_version").value = 1
                    overwrite_param(filepath, h)
                        

def shuffle_mdcs_live_trial(mdcs_outgoing_path):
    sp_folders = get_lvl1_folders(mdcs_outgoing_path)
    for t in sp_folders:
        for u in get_lvl1_folders(t[1]):
            depotid = u[0]
            depotpath = u[1]
            params = []
            modes = ["Live", "Trial"]
            for mode_f in modes:
                for v in get_lvl1_files(os.path.join(u[1], mode_f)):
                    filename = v[0]
                    filepath = v[1]

                    if is_trialable(filename):
                        params.append((filename, filepath))

            #params contain all the trialable parameters in the Live/Trial folders for this depot. shuffle.
            for param in params:
                r = randint(0,1)
                mode = modes[r]
                source_path = param[1]
                dest_path = os.path.join(depotpath, mode, param[0])
                if not source_path == dest_path:
                    #print("Moving [{}] to [{}]".format(source_path, dest_path))
                    os.rename(source_path, dest_path)
                    
def grab_ipts_and_compare(dagw_param_path):
    logging.info("Grabbing IPTs")
    
    #if any dump files are already there, delete them.
    trig1 = os.path.join(dagw_param_path, "IPT1.txt")
    trig2 = os.path.join(dagw_param_path, "IPT2.txt")
    dump1 = os.path.join(dagw_param_path, "IPT1-dump.txt")
    dump2 = os.path.join(dagw_param_path, "IPT2-dump.txt")
    if os.path.exists(trig1):
        os.remove(trig1)
    if os.path.exists(trig2):
        os.remove(trig2)
    if os.path.exists(dump1):
        os.remove(dump1)
    if os.path.exists(dump2):
        os.remove(dump2)

    #--
    
    f1 = open(trig1, "w+b")
    f1.close()
    f2 = open(trig2, "w+b")
    f2.close()

    #Wait for PRMServer to generate IPTs.
    time.sleep(75)

    if not os.path.exists(dump1):
        logging.error("{} does not exist!".format(dump1))
        return False
    if not os.path.exists(dump2):
        logging.error("{} does not exist!".format(dump1))
        return False

    same = filecmp.cmp(dump1, dump2, shallow=False)
    return same

def get_latest_file(path, prefix):
    f = [j for j in [i[0] for i in get_lvl1_files(path)] if j.startswith(prefix)]
    if len(f) == 0:
        return None
    name = max(f)
    return (name, os.path.join(path, name))

def dump_mdcs_pdts(mdcs_outgoing_path, copy_path):
    #OUTGOING
    #   gcm_pdt
    #   SP*
    #       DEPOT*
    #           sep_pdt
    #           LIVE
    #               param*
    #           TRIAL
    #               param*

    try:

        mdcs_copy_path = os.path.join(copy_path, "MDCS")

        gcm_pdt_path = os.path.join(mdcs_outgoing_path, "GCM_PDTA.SYS")
        shutil.copy2(gcm_pdt_path, mdcs_copy_path)
        
        sp_folders = get_lvl1_folders(mdcs_outgoing_path)
        for t in sp_folders:
            spid = t[0]

            sp_copy_path = os.path.join(mdcs_copy_path, spid)
            os.mkdir(sp_copy_path)
            
            for u in get_lvl1_folders(t[1]):
                depotid = u[0]
                depotpath = u[1]

                sep_pdt_path = os.path.join(depotpath, "SEP_PDTA.SYS")
                depot_copy_path = os.path.join(sp_copy_path, depotid)
                os.mkdir(depot_copy_path)
                shutil.copy2(sep_pdt_path, depot_copy_path)

##    except IOError as ie:
##        logging.error("Error - {}::{}::{}::{}".format(ie.errno, ie.strerror, ie.filename, ie.winerror))
    except Exception as e:
        logging.error(e)

def dump_dagw_pdts(dagw_outgoing_path, copy_path):
    #OUTGOING
    #   gcm_pdt
    #   SP*
    #       sep_pdt
    #       Live
    #           param*
    #       Trial
    #           param*

    try:

        dagw_copy_path = os.path.join(copy_path, "DAGW")

        gcm_pdt_path = os.path.join(dagw_outgoing_path, "GCM_PDTA.SYS")
        shutil.copy2(gcm_pdt_path, dagw_copy_path)
        
        sp_folders = get_lvl1_folders(dagw_outgoing_path)
        for t in sp_folders:
            spid = t[0]

            sp_copy_path = os.path.join(dagw_copy_path, spid)
            os.mkdir(sp_copy_path)

            sep_pdt_path = os.path.join(t[1], "SEP_PDTA.SYS")
            shutil.copy2(sep_pdt_path, sp_copy_path)

##    except IOError as ie:
##        logging.error("Error - {}::{}::{}::{}".format(ie.errno, ie.strerror, ie.filename, ie.winerror))
    except Exception as e:
        logging.error(e)

def compare_mdcs_and_dagw_pdts(mdcs_outgoing_path, dagw_outgoing_path):
    mdcs_pdt_path = os.path.join(mdcs_outgoing_path, "GCM_PDTA.SYS")
    dagw_pdt_path = os.path.join(dagw_outgoing_path, "GCM_PDTA.SYS")

    mdcs_header = read_param(mdcs_pdt_path, param_header)
    dagw_header = read_param(dagw_pdt_path, param_header)

    return get_child_element(mdcs_header, "param_version").value == get_child_element(dagw_header, "param_version").value


# * Select a push frequency from 0 secs (as fast as possible) to 60 secs?
# * Select a number of updates [2, 10]?
# * Loop below for number of update times.
# *     Shuffle params in mdcs/outgoing/sp/depot/[Live | Trial] folders. Take care not to shuffle non-trialable parameters.
# *     Increment versions of files and generate pdts in mdcs. ********DO NOT INCREMENT DAGWAPPA.SYS.********
# *     push down new gcm_pdt to dagw.
# * End Loop
# * Wait 5 minutes
# * Generate IPTs. Confirm that they match. If not, collect IPTs and Logs (Logs both in MDCS and DAGW). Save with the timestamp.
# 
# * Run the above in a loop.

def run_param_test(mdcs_param_path, dagw_param_path, dagw_log_paths, result_collect_path, push_freq_range, num_updates_range):
    #Set up log.
    logging.basicConfig(filename=os.path.join(result_collect_path, "test.log"), format='[%(asctime)s :%(lineno)s - %(funcName)20s()] %(message)s', level=logging.DEBUG)

    push_freq = randint(push_freq_range[0], push_freq_range[1])
    num_updates = randint(num_updates_range[0], num_updates_range[1])

    logging.info("Running param test with push_freq = {} and num_updates = {}".format(push_freq, num_updates))
    print("Running param test with push_freq = {} and num_updates = {}".format(push_freq, num_updates))

    mdcs_outgoing_path = os.path.join(mdcs_param_path, "outgoing")
    dagw_incoming_path = os.path.join(dagw_param_path, "incoming")
    dagw_outgoing_path = os.path.join(dagw_param_path, "outgoing")

    for i in range(0, num_updates):
        shuffle_mdcs_live_trial(mdcs_outgoing_path)
        increment_version_gun(mdcs_outgoing_path, dagw_incoming_path)
        time.sleep(push_freq)

    #wait 2 minutes.
    time.sleep(120)

    ipt_res = grab_ipts_and_compare(dagw_param_path)
    pdt_res = compare_mdcs_and_dagw_pdts(mdcs_outgoing_path, dagw_outgoing_path)

    #if not res:
    if not (ipt_res and pdt_res):

        #1. grab ipts.
        subdir_path = os.path.join(result_collect_path, datetime.now().strftime("%y_%m_%d__%H_%M_%S"))
        os.mkdir(subdir_path)
        if not os.path.exists(subdir_path):
            logging.error("Should have created path : {} . But, doesn't exist.".format(subdir_path))
            return False

        fd = open(os.path.join(subdir_path, "reason.txt"), "w")
        fd.write("push_freq = {}, num_updates = {}\n".format(push_freq, num_updates))
        if not ipt_res:
            fd.write("ipts dont match.\n")
        if not pdt_res:
            fd.write("pdt versions dont match.\n")
        fd.close()

        dump1 = os.path.join(dagw_param_path, "IPT1-dump.txt")
        dump2 = os.path.join(dagw_param_path, "IPT2-dump.txt")

        if os.path.exists(dump1):
            shutil.copy2(dump1, subdir_path)
        if os.path.exists(dump2):
            shutil.copy2(dump2, subdir_path)

        #create MDCS and DAGW subfolders.
        os.mkdir(os.path.join(subdir_path, "MDCS"))
        os.mkdir(os.path.join(subdir_path, "DAGW"))

        #2. grab dagw par logs.
        i = 1
        for dagw_log_path in dagw_log_paths:
            dagw_par_log = get_latest_file(dagw_log_path, "PAR")
            if not dagw_par_log == None:
                shutil.copy2(dagw_par_log[1], os.path.join(subdir_path, "DAGW", "PARLOG" + str(i) + ".log"))
            i = i + 1

        #4. dump mdcs pdts.
        dump_mdcs_pdts(mdcs_outgoing_path, subdir_path)

        #5. dump dagw pdts.
        dump_dagw_pdts(dagw_outgoing_path, subdir_path)

    else:
        logging.info("PDT versions match. IPTs match.")

def run_test_forever():
    while True:
        spaths = [#r'\\192.168.29.70\d$\AFC\MDCS\Parameters',
                  r'\\192.168.31.141\d$\Test\MDCS',
                  r'\\192.168.31.141\afc\Parameters',
                  r'\\192.168.31.138\d$\afc\Gateway\Logs',
                  r'\\192.168.31.139\d$\afc\Gateway\Logs']

        #map needed drives.
        for path in spaths:
            if not os.path.exists(path):
                subprocess.call(r'net use * {} /user:{} {}'.format(path, "sepuser", "pass1234"), shell=True)
        
##        try:
##            run_param_test(r'\\192.168.29.70\d$\AFC\MDCS\Parameters', r'\\192.168.29.70\d$\AFC\MDCS\Logs',
##                       r'\\192.168.31.141\afc\Parameters', [r'\\192.168.31.138\d$\afc\Gateway\Logs', r'\\192.168.31.139\d$\afc\Gateway\Logs'],
##                       r'D:\test_res', (0,300), (2,10))
##        except:
##            logging.error("Caught exception... Rerunning :)")

##        time.sleep(60)
      
        #try:
        run_param_test(r'\\192.168.31.141\d$\Test\MDCS', r'\\192.168.31.141\afc\Parameters',
                       [r'\\192.168.31.138\d$\afc\Gateway\Logs', r'\\192.168.31.139\d$\afc\Gateway\Logs'],
                       r'D:\test_res', (0,15), (2,5))
        #except:
            #logging.error("Caught exception... Rerunning :)")

        time.sleep(15)
        
##-------------------------------------------------------------------------------------------------##        
        
##def main():
##    outgoing_path = ""
##    path_prefix = ""
##
##    try:
##        opts, args = getopt.getopt(sys.argv[1:], "hl:p:", ["help", "location=", "prefix="])
##    except getopt.GetoptError as err:
##        print(err)
##        print("Usage : {} -l <folder> -p <prefix>".format(sys.argv[0]))
##        sys.exit(2)
##
##    for opt, arg in opts:
##        if opt in ("-h", "--help"):
##            print("Usage : {} -l <folder> -p <prefix>".format(sys.argv[0]))
##        elif opt in ("-l", "--location"):
##            outgoing_path = arg
##        elif opt in ("-p", "--prefix"):
##            path_prefix = arg
##
##    print("Creating PDTS for folder : {} , prefix = {}".format(outgoing_path, path_prefix))
##
##    create_bo_pdts(outgoing_path, path_prefix)
##
##    exit(0)

##def main():
##    outgoing_path = ""
##
##    try:
##        opts, args = getopt.getopt(sys.argv[1:], "hl:", ["help", "location="])
##    except getopt.GetoptError as err:
##        print(err)
##        print("Usage : {} -l <outgoing folder>".format(sys.argv[0]))
##        sys.exit(2)
##
##    for opt, arg in opts:
##        if opt in ("-h", "--help"):
##            print("Usage : {} -l <outgoing folder>".format(sys.argv[0]))
##        elif opt in ("-l", "--location"):
##            outgoing_path = arg
##
##    print("Creating PDTS for folder : {}".format(outgoing_path))
##
##    if not os.path.exists(outgoing_path):
##        subprocess.call(r'net use * {} /user:{} {}'.format(outgoing_path, "sepuser", "pass1234"), shell=True)
##        
##    create_mdcs_pdts(outgoing_path)
##
##    exit(0)

##def main():
##    mdcs_path = ""
##    dagw_path = ""
##    interval = 60
##
##    try:
##        opts, args = getopt.getopt(sys.argv[1:], "hm:g:i:", ["help", "mdcs=", "dagw=", "interval="])
##    except getopt.GetoptError as err:
##        print(err)
##        print("Usage : {} -m <mdcs outgoing folder> -g <dagw incoming folder> -i <interval>".format(sys.argv[0]))
##        sys.exit(2)
##
##    for opt, arg in opts:
##        if opt in ("-h", "--help"):
##            print("Usage : {} -m <mdcs outgoing folder> -g <dagw incoming folder> -i <interval>".format(sys.argv[0]))
##        elif opt in ("-m", "--mdcs"):
##            mdcs_path = arg
##        elif opt in ("-g", "--dagw"):
##            dagw_path = arg
##        elif opt in ("-i", "--interval"):
##            interval = int(arg)
##
##    while True:
##        if not os.path.exists(mdcs_path):
##            subprocess.call(r'net use * {} /user:{} {}'.format(mdcs_path, "sepuser", "pass1234"), shell=True)
##
##        if not os.path.exists(dagw_path):
##            subprocess.call(r'net use * {} /user:{} {}'.format(dagw_path, "sepuser", "pass1234"), shell=True)
##    
##        print("Running gun with mdcs_path = {}, dagw_path = {}, interval = {}".format(mdcs_path, dagw_path, interval))
##        increment_version_gun(mdcs_path, dagw_path)
##
##        h = read_param(os.path.join(mdcs_path, "GCM_PDTA.SYS"), param_header)
##        version = get_child_element(h, "param_version").value
##
##        print("Done... Current MDCS GCM_PDTA.SYS version = {}".format(version))
##        print("Sleeping for {} seconds".format(interval))
##        time.sleep(interval)
##
##    exit(0)

def main():
    pass
    #run_test_forever()
            
if __name__ == "__main__":
    main()

import argparse
import os
import re

# ...............................................
pkg_filename_components=(
    '^(?P<pkgname>.*?)', 
    '(?P<version>', 
        '\-(?P<major>\d*)', 
        '\.(?P<minor>\d*)', 
        '\.(?P<patch>\d*))', 
    '(?P<release>', 
        '\-(?P<rmajor>\d*)?', 
        '(\.(?P<rminor>\.\d*))?', 
        '(\.(?P<rpatch>\.\d*))?',
    ')?', 
    '(?P<osver>.*(\.el7)', 
        '(\_(?P<major2>\d*)?',
        '(\.)?', 
        '(?P<minor2>\d*)?)?',
    ')?', 
    '(?P<arch>\.i686|\.x86_64|\.noarch)?', 
    '(\.rpm)$'
)
PKG_REGEX = ''.join(pkg_filename_components)
PRIMARY_DELIMITER = '-'
SECONDARY_DELIMITER = '.'

# ...............................................
def parse_version(vstring, delimiter):
    vmajor = vminor = vpatch = 0
    vparts = vstring.split(delimiter)
    vmajor = vparts[0]
    try:
        vminor = vparts[1]
        try:
            vpatch = vparts[2]
        except:
            pass
    except:
        pass
    return vmajor, vminor, vpatch

# ...............................................
def disect_rest(restparts):
    elmajor = elminor = None
    arch = ''
    leftovers = []
    # Discard extension
    if restparts[-1] == 'rpm':
        restparts = restparts[:-1]
    # Look for Enterprise Linux or Centos version
    for i in range(len(restparts)):
        if restparts[i].startswith('el'):
            sidx = restparts[i].find('_')
            if sidx >= 0:
                elmajor = restparts[i][sidx+1:]
            restparts = restparts[i+1:]
            break
        else:
            leftovers.append(restparts[i])
    if elmajor is not None and restparts[0][0].isdigit():
        elminor = restparts[0]
        restparts = restparts[1:]
    if elmajor is None:
        elmajor = 0
    if elminor is None:
        elminor = 0
    # Get architecture
    for i in range(len(restparts)):
        if restparts[i] not in ('x86_64', 'i686', 'noarch'):
            leftovers.append(restparts[i])
        else:
            arch = restparts[i]
            break
    restparts = restparts[i+1:]
    
    if restparts:
        print('There are still parts {}!'.format(restparts))
        leftovers.extend(restparts)
    
    return (elmajor, elminor), arch, leftovers
            
# ...............................................
def get_parts_starting_with(somestring, delimiter, desired='digit'):
    parts = somestring.split(delimiter)
    desired_parts = []
    for i in range(len(parts)):
        firstch = parts[i][0]
        if ((desired == 'digit' and firstch.isdigit()) or
            (desired == 'char' and firstch.isalpha()) ):
            desired_parts.append(parts[i])
        else:
            parts = parts[i:]
            break
    desired_string = delimiter.join(desired_parts)
    return desired_string, parts
    
# ...............................................
def parse_package_filename(fname):
    basefname = os.path.basename(fname)    
    pkgname, parts = get_parts_starting_with(
        basefname, PRIMARY_DELIMITER, desired='char')
    
    # sections are all delimited by '-'
    version_section = parts[0]
    parts = parts[1:]
    versions = parse_version(version_section, SECONDARY_DELIMITER)
    release_rest_section = parts[0]
    tail_sections = parts[1:]
    
    relstring, restparts = get_parts_starting_with(
        release_rest_section, SECONDARY_DELIMITER, desired='digit')
    releases = parse_version(relstring, SECONDARY_DELIMITER)
    
    el_versions, arch, leftovers = disect_rest(restparts)
    
    if tail_sections:
        tail_parts = []
        for sec in tail_sections:
            smpts = sec.split(SECONDARY_DELIMITER)
            tail_parts.extend(smpts)
        leftovers.extend(tail_parts)
    
    print('pkgname {}, arch {}, leftovers {}'.format(pkgname, arch, leftovers))
    print ('version: {} {} {}'.format(versions[0], versions[1], versions[2])) 
    print ('release: {} {} {}'.format(releases[0], releases[1], releases[2])) 
    print ('el_ver: {} {}'.format(el_versions[0], el_versions[1]))
    print ('leftovers: {}'.format(leftovers))
    
    return (pkgname, versions, releases, el_versions, arch, leftovers)
    
            
# ...............................................
def re_parse_package_filename(fname):
    basefname = os.path.basename(fname)
    vermajor = verminor = verpatch = relmajor = relminor = relpatch = None
    othermajor = otherminor = arch = None
    p = re.compile(PKG_REGEX)
    m = p.match(basefname)
    if m is None:
        print('Failed to parse {}'.format(fname))
    else:
        parts = m.groups()
        (pkgname, _, vermajor, verminor, verpatch, _, relmajor, relminor, relpatch, 
         _, _, _, _, _, othermajor, _, otherminor, arch, _, ) = parts     
        versions = (vermajor, verminor, verpatch)
        releases = (relmajor, relminor, relpatch)
        others = (othermajor, otherminor)

    return pkgname, versions, releases, others, arch

# ...............................................
def main():
    parser = argparse.ArgumentParser(
        description=('Find the latest rpm file for a package.'))
    parser.add_argument(
        'pkgname', type=str, help='RPM package to find latest for')
    args = parser.parse_args()


    (pkgname, versions, releases, el_versions, arch, 
     othermeta) = parse_package_filename(args.pkgname)
        
# .............................................................................
if __name__ == '__main__':
    main()

"""
import find_version
import imp

pkgname = 'python-perf'
pth = 'mirror.oss.ou.edu/centos/7/updates/x86_64/Packages/'
PRIMARY_DELIMITER = '-'
SECONDARY_DELIMITER = '.'
manyfnames = ['bind-pkcs11-libs-9.11.4-16.P2.el7_8.2.x86_64.rpm',
             'bind-pkcs11-libs-9.11.4-16.P2.el7.noarch.rpm',
             'bind-devel-9.11.4-16.i686.rpm',
             'bind-devel-9.11.4-16.el7.i686.rpm',
             'bind-devel-9.11.4-16.P2.el7_8.3.x86_64.rpm',
             'bind-devel-9.11.4-16.P2.el7.x86_64.rpm',
             'bind-devel-9.11.4-16.P2.el7.rpm',
             'python-perf-3.10.0-1127.10.1.el7.x86_64.rpm',
             'python-perf-3.10.0-1127.8.2.el7.x86_64.rpm',
             'bind-export-libs-9.11.4-16.P2.el7_8.6.x86_64.rpm',
             'tzdata-2020a-1.el7.noarch.rpm',
             'telnet-0.17-65.el7_8.x86_64.rpm',
             'systemd-sysv-219-73.el7_8.6.x86_64.rpm',
             'systemd-python-219-73.el7_8.8.x86_64.rpm',
             'systemd-libs-219-73.el7_8.6.i686.rpm',
             'systemd-devel-219-73.el7_8.5.x86_64.rpm',
             'systemd-resolved-219-73.el7_8.6.i686.rpm',
             'sos-collector-1.8-2.el7_8.noarch.rpm',
             'rdma-core-devel-22.4-2.el7_8.x86_64.rpm',
             'rdma-core-devel-22.4-2.el7_8.x86_64.rpm',
             'ntpdate-4.2.6p5-29.el7.centos.2.x86_64.rpm',
             'ntp-doc-4.2.6p5-29.el7.centos.2.noarch.rpm',
             'microcode_ctl-2.1-61.10.el7_8.x86_64.rpm',
             'lvm2-python-boom-0.9-25.el7_8.1.noarch.rpm',
             'librdmacm-22.4-2.el7_8.i686.rpm',
             'libicu-devel-50.2-4.el7_7.x86_64.rpm',
             'libicu-devel-50.2-4.el7_7.x86_64.rpm',
             'libibverbs-22.4-2.el7_8.x86_64.rpm',
             'libibumad-22.4-2.el7_8.x86_64.rpm',
             'libgudev1-219-73.el7_8.8.i686.rpm',
             'ibacm-22.4-2.el7_8.x86_64.rpm',
             'firefox-68.6.0-1.el7.centos.i686.rpm',
             'binutils-devel-2.27-43.base.el7_8.1.i686.rpm',
             'binutils-devel-2.27-43.base.el7_8.1.i686.rpm']


manyfnames = ['ntp-doc-4.2.6p5-29.el7.centos.2.noarch.rpm', 
             'ntpdate-4.2.6p5-29.el7.centos.2.x86_64.rpm',
             'firefox-68.6.0-1.el7.centos.i686.rpm']

basefname = manyfnames[0]
pkgname, parts = get_parts_starting_with(
    basefname, PRIMARY_DELIMITER, desired='char')    
version_section = parts[0]
parts = parts[1:]
versions = parse_version(version_section, SECONDARY_DELIMITER)
release_rest_section = parts[0]
tail_sections = parts[1:]
relstring, restparts = get_parts_starting_with(
    release_rest_section, SECONDARY_DELIMITER, desired='digit')
releases = parse_version(relstring, SECONDARY_DELIMITER)
el_versions, arch, leftovers = disect_rest(restparts)
if tail_sections:
    tail_parts = []
    for sec in tail_sections:
        smpts = sec.split(SECONDARY_DELIMITER)
        tail_parts.extend(smpts)
    leftovers.extend(tail_parts)
print('pkgname {}, arch {}, othermeta {}'.format(pkgname, arch, othermeta))
print ('version: {} {} {}'.format(versions[0], versions[1], versions[2])) 
print ('release: {} {} {}'.format(releases[0], releases[1], releases[2])) 
print ('el_ver: {} {}'.format(el_versions[0], el_versions[1]))
print ('leftovers: {}'.format(leftovers))




for basefname in manyfnames:
    pkgname, parts = get_parts_starting_with(
        basefname, PRIMARY_DELIMITER, desired='char')    
    version_section = parts[0]
    parts = parts[1:]
    versions = parse_version(version_section, SECONDARY_DELIMITER)
    release_rest_section = parts[0]
    tail_sections = parts[1:]
    relstring, restparts = get_parts_starting_with(
        release_rest_section, SECONDARY_DELIMITER, desired='digit')
    releases = parse_version(relstring, SECONDARY_DELIMITER)
    el_versions, arch, leftovers = disect_rest(restparts)
    if tail_sections:
        tail_parts = []
        for sec in tail_sections:
            smpts = sec.split(SECONDARY_DELIMITER)
            tail_parts.extend(smpts)
        leftovers.extend(tail_parts)
    print(basefname)
    print('   {}, arch {}, othermeta {}'.format(pkgname, arch, othermeta))
    print('   version: {} {} {}'.format(versions[0], versions[1], versions[2])) 
    print('   release: {} {} {}'.format(releases[0], releases[1], releases[2])) 
    print('   el_ver: {} {}'.format(el_versions[0], el_versions[1]))
    print('   leftovers: {}'.format(leftovers))










imp.reload(find_version)

for fn in fnames:
    ((vermajor, verminor, verpatch), (relmajor, relminor, relpatch), 
     (othermajor, otherminor), arch) = find_version.parse_packagename(fn)    
    print (vermajor, verminor, verpatch, relmajor, relminor, relpatch, 
           othermajor, otherminor, arch)


p = re.compile(PKG_REGEX)
m = p.match(fname)
parts = m.groups()
(pkgname, _, vermajor, verminor, verpatch, _, relmajor, relminor, relpatch, 
 _, _, _, othermajor, _, otherminor, arch, _, ) = parts     
vermajor = interpret_ver(vermajor)
verminor = interpret_ver(verminor)
verpatch = interpret_ver(verpatch)
relmajor = interpret_ver(relmajor)
relminor = interpret_ver(relminor)
relpatch = interpret_ver(relpatch)
othermajor = interpret_ver(othermajor)
otherminor = interpret_ver(otherminor)


"""
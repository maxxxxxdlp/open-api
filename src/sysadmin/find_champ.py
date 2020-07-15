import argparse
import glob
import os

from find_version import parse_package_filename
# ...............................................
# ...............................................    
def compare_elt(current, champ):
    """Return an integer indicating whether the current version indicator is 
    larger, equal, or smaller than the reigning champ.
    
    Args:
        current: value to be compared
        champ: value to be compared against

    Returns:
        1 if current is larger than champ
        0 if current = champ
        -1 if current is smaller than champ

    Note:
        None is interpreted as smaller than not None
    """
    if champ is None:
        if current is None:
            return 0
        return 1

    if current is None:
        return -1

    if current > champ:
        return 1
    elif current < champ:
        return -1
    else:
        return 0

# ...............................................    
def compare_elements(ver_current, ver_champ):
    """Return an integer indicating whether the current version indicators are 
    larger, equal, or smaller than the reigning champ.
    
    Args:
        ver_current: major, minor, patch values to be compared
        ver_champ: major, minor, patch values to be compared against

    Returns:
        1 if current is larger than champ
        0 if current = champ
        -1 if current is smaller than champ
    """
    if len(ver_champ) not in (2,3) or len(ver_current) not in (2,3):
        raise Exception('Wrong number of version parts')
    major_champ = minor_champ = patch_champ = None
    major_curr = minor_curr = patch_curr = None
    try:
        major_champ, minor_champ, patch_champ = ver_champ
    except:
        major_champ, minor_champ = ver_champ[0], ver_champ[1]

    try:
        major_curr, minor_curr, patch_curr = ver_current
    except:
        major_curr, minor_curr = ver_current[0], ver_current[1]

    res = compare_elt(major_curr, major_champ)
    if res in (1, -1):
        return res
    # Major version is equal, check minor
    else:
        res = compare_elt(minor_curr, minor_champ)
        return res

# ...............................................    
def compare_all_parts(current_all_parts, champ_all_parts, architecture=None):
    """Return an integer indicating whether the current version indicators
    (major/minor/patch of version, release, other) are larger, equal, or 
    smaller than the reigning champ.
    
    Args:
        ver_current: major, minor, patch values to be compared
        ver_champ: major, minor, patch values to be compared against

    Returns:
        1 if current is larger than champ
        0 if current = champ
        -1 if current is smaller than champ
    """
    ver_current, rel_current, other_current, arch_current = current_all_parts
    ver_champ, rel_champ, other_champ, arch_champ = champ_all_parts    
    
    if architecture is not None and architecture != arch_current:
        return -1
    else:
        res = compare_elements(ver_current, ver_champ)
        if res in (-1,1):
            return res
        # Versions are equal, check release
        else:
            res = compare_elements(rel_current, rel_champ)
            if res in (-1,1):
                return res
            # Versions are equal, check release
            else:
                res = compare_elements(other_current, other_champ)
                return res

# ...............................................
def find_latest_package_file(pkgname, pth, architecture=None):
    champ_basename = champ_file = None
    champ_all_parts = None
    champ_arch = None
    possible_fnames = glob.glob(os.path.join(pth, '{}*rpm'.format(pkgname)))
    for fname in possible_fnames:
        basefname = os.path.basename(fname)
        (file_pkgname, version_parts, release_parts, other_parts, 
         arch) = parse_package_filename(basefname)
        # Glob returns additional files with same prefix
        if file_pkgname == pkgname:
            current_all_parts = (version_parts, release_parts, other_parts, arch)
            if champ_file is None:
                if architecture is None or architecture == arch:
                    champ_file = fname
                    champ_all_parts = current_all_parts
                    champ_arch = arch
            else:
                result = compare_all_parts(
                    current_all_parts, champ_all_parts, architecture=arch)
                if result == 1:
                    champ_file = fname
                    champ_all_parts = current_all_parts
                    champ_arch = arch
    if champ_file is not None:
        champ_basename = os.path.basename(champ_file)
    return champ_basename 


# ...............................................
def main():
    parser = argparse.ArgumentParser(
        description=('Find the latest rpm file for a package.'))
    parser.add_argument(
        'pkgname', type=str, help='RPM package to find latest for')
    parser.add_argument(
        'path', type=str, help='Path to RPM packages')
    args = parser.parse_args()

    champ_file = find_latest_package_file(args.pkgname, args.path)
    
    print (champ_file)
    
# .............................................................................
if __name__ == '__main__':
    main()

"""
import imp, glob, os, re
import find_version
import find_champ

imp.reload(find_version)
imp.reload(find_champ)
from find_version import *
from find_champ import *


pth = '/root/mirror.oss.ou.edu/centos/7/updates/x86_64/Packages/'
basenames = ['bind-pkcs11-libs-9.11.4-16.P2.el7_8.2.x86_64.rpm',
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

pkgname = pnames[0]

# champ_file = find_champ.find_latest_package_file(pkgname, pth)

champ_basename = champ_file = None
champ_all_parts = None
champ_arch = None
# possible_fnames = glob.glob(os.path.join(pth, '{}*rpm'.format(pkgname)))
possible_fnames = [os.path.join(pth, bname for bname in basenames]
# for fname in possible_fnames:
fname = possible_fnames[0]
(file_pkgname, version_parts, release_parts, other_parts, arch) = find_version.parse_package_filename(fname)
 


 
if file_pkgname == pkgname:
    current_all_parts = (version_parts, release_parts, other_parts)
    if champ_file is None:
        champ_file = fname
        champ_all_parts = current_all_parts
    else:
        result = compare_all_parts(current_all_parts, champ_all_parts)
        if result == 1:
            champ_file = fname
            champ_all_parts = current_all_parts


"""
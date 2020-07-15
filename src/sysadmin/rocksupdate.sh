set_defaults () {
    user=`/bin/whoami`
    thisdir=`/bin/pwd`
    if [[ "$user" != "root" ]]; then 
        echo 'rocksupdate must be run by root user'
    fi
    if [[ "$thisdir" != "/root" ]]; then 
        'rocksupdate must be run in /root directory, not $thisdir'
    fi

    base_addr=mirror.oss.ou.edu/centos
    osversion=7
    version=`date +%F`

    DL_PATH=/root/${base_addr}/${osversion}/updates/x86_64/Packages
    CONTRIB_PATH=/state/partition1/rocks/install/contrib/7.0/x86_64/RPMS
    FILE_START_IDX=$((${#DL_PATH} + 2))
    REGEX_PAT='(.+)(\-)(\d*.+)(\-)(.+)'
    
    echo "-- enable modules"  | tee -a $LOG
    source /usr/share/Modules/init/bash
    module load opt-python    
    PYBIN=/opt/python/bin/python3.6

    # python script
    SCRIPT_DIR=/state/partition1/git/issues/src/maintenance
    FIND_VERPY=$SCRIPT_DIR/find_version.py
    FIND_CHAMP=$SCRIPT_DIR/find_champ.py
    
#     LOG=`/bin/basename $0`.log
    OUT_FNAME=required_packages.txt
    /bin/rm -f $OUT_FNAME
    /bin/touch $LOG
    LOG=rocksupdate.log
    /bin/rm -f $LOG
    /bin/touch $LOG
}


download_updates () {
    baseurl=http://$base_addr
    osversion=7
    version=`date +%F`
    rocks create mirror ${baseurl}/${osversion}/updates/x86_64/Packages/ rollname=Updates-CentOS-${osversion} version=${version}
}

# 
# find_latest_pkgfile () {
#     pkgname=$1
#     
#     # find multiple versions of same update, plus pkgs starting with same name
#     PKG_FILES=$DL_PATH/$pkgname*rpm
#     pkg_count=${#PKG_FILES[@]}
#     
#     for currf in $PKG_FILES
#         do
#             file_pkgname_ver=`get_package_name_version $currf`            
#             file_pkgname=`echo $file_pkgname_ver | awk '{print $1}'`
#             if [ $file_pkgname = $pkgname ]; then
#                 filelen=${#currf}            
#                 base_file_name=$(echo $currf | cut -c$FILE_START_IDX-$filelen)
#                 if [ -z ${latest_file} ] ; then
#                     latest_file=$base_file_name
#                     latest_ver=`$PYBIN $FIND_VERPY $base_file_name`
#                 else
#                     ver_output=`get_latest_version $base_file_name $latest_ver`
#                     if [ $ver_output != 0 ]; then
#                         latest_file=$base_file_name
#                         latest_ver=`echo $ver_output`
#                 fi
#             fi
#         done
#         echo "Latest version of $pkgname is $latest_ver in $latest_file"
#     echo $latest_file
# }

get_package_name_version () {
    fname=$1
    
    filelen=${#fname}            
    base_file_name=$(echo $fname | cut -c$FILE_START_IDX-$filelen)
    [[ $base_file_name =~ $REGEX_PAT ]]
    pkgname=${BASH_REMATCH[1]}
    ver=${BASH_REMATCH[3]}    
    echo $pkgname  $ver
}


# Find updates for installed packages
find_needed_packages () {
    # these are filename prefixes
    echo "-- save updates for installed packages ..."
    FILES=`/bin/ls -rw1 $DL_PATH/*rpm`
    curr_pkgname=nothing
    for fname in $FILES
        do
            pkgname_ver=`get_package_name_version $fname`
            pkgname=`echo $pkgname_ver | awk '{print $1}'`
            # process only first file for given package, we get latest version
            if [[ $curr_pkgname == $pkgname ]]; then
                echo "checking file: $fname"
            else
                echo ""
                echo "checking file: $fname"
                curr_pkgname=$pkgname
                pcnt=`/usr/bin/rpm -qa | /usr/bin/grep ^$pkgname | /usr/bin/wc -l`
                if [[ ${pcnt} == 0 ]]; then
                    echo "  Remove not installed: $pkgname"
                    #/usr/bin/rm -f $DL_PATH/$pkgname*
                else
                    $PYBIN $FIND_CHAMP $pkgname $DL_PATH | tee -a $OUT_FNAME
                    echo "  Update $pkgname"
                fi
                echo ""
            fi
        done
}


# main
set_defaults
download_updates
delete_unecessary_packages
delete_older_updates
find_packages

# (cd /export/rocks/install; rocks create distro)
# yum clean all
# yum check-updates >> $LOG


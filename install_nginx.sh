#!/bin/bash

# Created by Tan.Zhihen
# Func: Install nginx and optimize basic setting
# OS: Amazon Linux AMI(Not Amazon Linux 2 AMI)
# Udated: 20190206
# Usage: sh install_nginx.sh

pre_check(){
    # Check if OS version match
    if ! `grep 'NAME="Amazon Linux AMI"' /etc/os-release > /dev/null 2>&1`
        then
        echo "OS version is not Amazon Linux AMI"
        exit 1
    fi

    # Check if nginx has been installed
    rpm -qa | grep nginx > /dev/null 2>&1 && echo "Nginx has been installed." && exit 0
}

install_nginx(){
    yum -y install nginx
}

setup_config(){
    date_time=`date '+%Y%m%d_%H%M%S'`
    
    # setup nginx.conf
    conf_file='/etc/nginx/nginx.conf'
    cp ${conf_file} ${conf_file}.${date_time}

    # basic setting

    # nworker_rlimit_nofile:the limit on the largest size of a core file (RLIMIT_CORE) for worker processes. 
    # Used to increase the limit without restarting the main process.
    sed -i '/pid/a\\nworker_rlimit_nofile 100000;' ${conf_file}

    # worker_connections:Determines how many clients will be served by each worker process.
    # (Max clients = worker_connections * worker_processes)
    # Should be equal to `ulimit -n`
    sed -i 's/worker_connections.*/worker_connections 65535;/' ${conf_file}

    # multi_accept:Let each process accept multiple connections.
    # Accept as many connections as possible, after nginx gets notification
    # about a new connection.
    # May flood worker_connections, if that option is set too low.
    #
    # epoll:Preferred connection method for newer linux versions.
    # Essential for linux, optmized to serve many clients with each thread.
    sed -i '/worker_connections/a\    multi_accept on;\n    use epoll;' ${conf_file}

    # gzip setting
    sed -i '/types_hash_max_size/a\\n    gzip on;\n    gzip_min_length 1100;\n    gzip_buffers 4 32k;\n    gzip_types text/plain text/xml text/css application/x-javascript application/javascript application/ecmascript application/json application/xml application/rss+xml text/javascript;' ${conf_file}

    # open_file_cache setting
    sed -i '/gzip_types/a\\n    open_file_cache max=1000 inactive=20s;\n    open_file_cache_valid 60s;\n    open_file_cache_min_uses 1;\n    open_file_cache_errors on;' ${conf_file}

    # hide nginx version
    sed -i '/open_file_cache_errors/a\\n    server_tokens off;' ${conf_file}

    chkconfig nginx on

    echo -e "\n====== ${conf_file} <> ${conf_file}.${date_time} ======"
    diff ${conf_file} ${conf_file}.${date_time}

    # change /var/log/nginx permission so that can be access by any user
    chmod o+rx /var/log/nginx

    # disabled mail of root from logrotate.d
    sed -i 's#reopen_logs#reopen_logs > /dev/null 2>\&1#' /etc/logrotate.d/nginx
}

restart_service(){
    echo -e "\n====== Starting service ======"

    # restart nginx
    /etc/init.d/nginx restart
}

main(){
    pre_check

    yum info nginx
    while true; do
        read -p "Install this version?[Y/N]" yn
        case $yn in
            [Yy]* ) install_nginx
                    setup_config
                    restart_service
                    break
                    ;;
            [Nn]* ) exit 0;; 
            * ) echo "Please answer yes or no.";;
        esac
    done
}

main
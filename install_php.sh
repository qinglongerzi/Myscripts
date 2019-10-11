#!/bin/bash

# Created by Tan.Zhihen
# Func: Install PHP&PHP-fpm and optimize basic setting
# OS: Amazon Linux AMI(Not Amazon Linux 2 AMI)
# Udated: 20191008
# Usage: sh install_php.sh


install_php(){
    # get version from args
    version=$1

    # install scl which will be used while installing php
    # liblzf is for php7.3
    rpm -qa | grep scl-utils > /dev/null 2>&1 || yum -y install --enablerepo=epel scl-utils liblzf

    # install php and modules
    yum -y install php${version} \
                   php${version}-fpm \
                   php${version}-opcache \
                   php${version}-mbstring \
                   php${version}-mcrypt \
                   php${version}-redis \
                   php${version}-igbinary \
                   php${version}-pdo \
                   php${version}-mysqlnd \
                   php${version}-snmp \
                   php${version}-process \
                   php${version}-devel \
                   php${version}-gd \
                   php${version}-soap \
                   php${version}-memcached
}


setup_config(){
    date_time=`date '+%Y%m%d_%H%M%S'`

    # setup php-fpm
    conf_file=`readlink -f /etc/php-fpm.d/www.conf`
    cp ${conf_file} ${conf_file}.${date_time}

    sed -i '/\[www\]/a env[NSS_SDB_USE_CACHE] = "YES"' ${conf_file}
    sed -i 's/^user =.*/user = nginx/' ${conf_file}
    sed -i 's/^group =.*/group = nginx/' ${conf_file}
    sed -i 's#^listen =.*#listen = /var/run/php-fpm/php-fpm.sock#' ${conf_file}
    sed -i 's/^;listen.owner =.*/;listen.owner = nginx/' ${conf_file}
    sed -i 's/^;listen.group =.*/;listen.group = nginx/' ${conf_file}
    sed -i 's/^;listen.mode =.*/listen.mode = 0660/' ${conf_file}
    sed -i 's/^pm = dynamic/pm = static/' ${conf_file}
    sed -i 's/^pm.max_children = .*/pm.max_children = 10/' ${conf_file}
    sed -i -r 's/^(pm.start_servers = .*)/;\1/' ${conf_file}
    sed -i -r 's/^(pm.min_spare_servers = .*)/;\1/' ${conf_file}
    sed -i -r 's/^(pm.max_spare_servers = .*)/;\1/' ${conf_file}
    sed -i 's/^;pm.process_idle_timeout = .*/pm.process_idle_timeout = 30s/' ${conf_file}
    sed -i 's/^;pm.max_requests = .*/pm.max_requests = 500/' ${conf_file}
    sed -i 's/^;request_terminate_timeout = .*/request_terminate_timeout = 60/' ${conf_file}
    sed -i 's/^;catch_workers_output = .*/catch_workers_output = yes/' ${conf_file}
    sed -i -r 's/^;(php_value\[opcache.file_cache\] .*)/\1/' ${conf_file}

    chown -R root.nginx /var/lib/php/*

    chkconfig php-fpm on

    echo -e "\n====== ${conf_file} <> ${conf_file}.${date_time} ======"
    diff ${conf_file} ${conf_file}.${date_time}

    # setup php.ini
    conf_file=`readlink -f /etc/php.ini`
    cp ${conf_file} ${conf_file}.${date_time}

    sed -i 's/^expose_php = .*/expose_php = Off/' ${conf_file}
    # app timeout default value 30s. max_execution_time must less than 30s.
    sed -i 's/^max_execution_time = .*/max_execution_time = 15/' ${conf_file}
    sed -i 's/^memory_limit = .*/memory_limit = 512M/' ${conf_file}
    sed -i 's/^html_errors = .*/html_errors = Off/' ${conf_file}
    sed -i 's#^;error_log = syslog#error_log = /var/log/nginx/php_errors.log#' ${conf_file}
    sed -i 's#^;date.timezone =.*#date.timezone = Asia/Tokyo#' ${conf_file}
    sed -i 's/^mysqli.reconnect = .*/mysqli.reconnect = On/' ${conf_file}
    sed -i 's/^;mbstring.language = .*/mbstring.language = Japanese/' ${conf_file}
    sed -i 's/^;mbstring.internal_encoding =.*/mbstring.internal_encoding = UTF-8/' ${conf_file}
    sed -i 's#^;session.save_path = .*#session.save_path = /var/lib/php/session#' ${conf_file}
    sed -i 's/^;session.cookie_secure =.*/session.cookie_secure = 1/' ${conf_file}

    echo -n "\n====== ${conf_file} <> ${conf_file}.${date_time} ======"
    diff ${conf_file} ${conf_file}.${date_time}

    # setup 10-opcache.ini
    conf_file=`readlink -f /etc/php.d/10-opcache.ini`
    cp ${conf_file} ${conf_file}.${date_time}

    sed -i 's/^opcache.enable=.*/opcache.enable=1/' ${conf_file}
    sed -i 's/^;opcache.enable_cli=.*/opcache.enable_cli=1/' ${conf_file}
    sed -i 's/^opcache.memory_consumption=.*/opcache.memory_consumption=128/' ${conf_file}
    sed -i 's/^opcache.interned_strings_buffer=.*/opcache.interned_strings_buffer=8/' ${conf_file}
    sed -i 's/^opcache.max_accelerated_files=.*/opcache.max_accelerated_files=4000/' ${conf_file}
    sed -i 's/^;opcache.revalidate_freq=.*/opcache.revalidate_freq=60/' ${conf_file}
    sed -i 's/^;opcache.fast_shutdown=.*/opcache.fast_shutdown=1/' ${conf_file}

    echo -e "\n====== ${conf_file} <> ${conf_file}.${date_time} ======"
    diff ${conf_file} ${conf_file}.${date_time}


    conf_file="/etc/nginx/conf.d/service.conf.example"
    if [ -f ${conf_file} ]
        then
        mv ${conf_file} ${conf_file}.${date_time}
    fi
    cat > ${conf_file} << EOF
server {
    listen 80;
    server_name a.com;
    return 301 https://\$host\$request_uri;
}
server {
    listen 443 ssl;
    ssl on;
    server_name a.com;

    set \$validURL "";

    ssl_certificate /etc/nginx/conf.d/ssl/a.com.crt;
    ssl_certificate_key /etc/nginx/conf.d/ssl/a.com.key;
    ssl_protocols        TLSv1 TLSv1.1 TLSv1.2;
    ssl_ciphers          "EECDH+ECDSA+AESGCM EECDH+aRSA+AESGCM EECDH+ECDSA+SHA384 EECDH+ECDSA+SHA256 EECDH+aRSA+SHA384 EECDH+aRSA+SHA256 EECDH+aRSA+RC4 EECDH EDH+aRSA RC4 !aNULL !eNULL !LOW !3DES !MD5 !EXP !PSK !SRP !DSS !RC4";
    ssl_dhparam /etc/nginx/conf.d/ssl/dhparam.pem;
    ssl_session_cache    shared:SSL:10m;
    ssl_session_timeout  10m;
    add_header Strict-Transport-Security "max-age=15768000; includeSubdomains";
    add_header X-Frame-Options "SAMEORIGIN";
    add_header Content-Security-Policy "default-src 'self' 'unsafe-inline' 'unsafe-eval' \$validURL";
    add_header X-Content-Security-Policy "allow 'self' 'unsafe-inline' 'unsafe-eval' \$validURL";
    add_header X-WebKit-CSP "default-src 'self' 'unsafe-inline' 'unsafe-eval' \$validURL";
    add_header X-XSS-Protection "1; mode=block";
    charset utf8;

    root /var/www/html;

    location / {
        index  index.php index.html index.htm;

        ## for auth basic
        # auth_basic "Restricted";
        # auth_basic_user_file /etc/nginx/.htpasswd;

        ## for laravel or wordpress
        try_files \$uri \$uri/ /index.php?\$query_string;
    }
    location ~ \.php$ {
        fastcgi_pass   unix:/var/run/php-fpm/php-fpm.sock;
        fastcgi_index  index.php;
        fastcgi_param  NSS_SDB_USE_CACHE yes;
        fastcgi_param  SCRIPT_FILENAME  \$document_root\$fastcgi_script_name;
        include        fastcgi_params;
    }
    # Deny all attempts to access hidden files such as .htaccess, .htpasswd, .DS_Store (Mac).
    location ~ /\. {
        deny all;
    }
}
EOF

    echo "========== NOTICE =========="
    echo "'$conf_file' is Created! Please create '/etc/nginx/conf.d/ssl/dhparam.pem' manually if you use ssl."
    echo ">　openssl dhparam 2048 -out /etc/nginx/conf.d/ssl/dhparam.pem"
    echo "If php7.3 installed, please run the command as bellow."
    echo "> yum install php7-pear gcc zlib-devel libmemcached-devel"
    echo "> pecl7 channel-update pecl.php.net"
    echo "> pecl7 install memcached"
    echo "input 'no --disable-memcached-sasl' and press enter. Also press enter for others."
    echo "> cd /etc/php.d"
    echo "> echo 'extension=memcached.so' >> 90-memcached.ini"

    # change /var/www permission so that can be access by any user
    chmod 777 /var/www
    chmod +t /var/www

}


restart_service(){
    echo -e "\n====== Starting service ======"

    # restart php-fpm
    /etc/init.d/php-fpm restart

    # restart nginx
    /etc/init.d/nginx restart
}


remove_php(){
    # remove all php package
    yum -y remove php*

    echo "PHP remove complete."
}


pre_check(){
    # If OS version not match, exit
    if ! `grep 'NAME="Amazon Linux AMI"' /etc/os-release > /dev/null 2>&1`
        then
        echo "OS version is not Amazon Linux AMI"
        exit 1
    fi

    # If nginx has not been installed, exit
    if ! `rpm -qa | grep nginx > /dev/null 2>&1`
        then
        echo "Please install nginx!"
        exit 1
    fi

    # If PHP has been installed, remove or exit
    if `rpm -qa | grep php > /dev/null 2>&1`
        then
        echo "PHP has been installed."
        while true; do
            read -p "Remove PHP already installed?[Y/N]" yn
            case $yn in
                [Yy]* ) remove_php; break;;
                [Nn]* ) exit 0;; 
                * ) echo "Please answer yes or no.";;
            esac
        done
    fi
}


main(){
    pre_check
    
    echo "Please select php version to install:"
    echo '1) 7.0'
    echo '2) 7.1'
    echo '3) 7.2'
    echo '4) 7.3'
    while true; do
        read -p "Please input number[1~3]" v
        case $v in
            1 ) php_ver="70"; break;;
            2 ) php_ver="71"; break;;
            3 ) php_ver="72"; break;;
            4 ) php_ver="73"; break;;
            * ) echo "Please input available number!";;
        esac
    done

    yum info php${php_ver}
    while true; do
        read -p "Install this version?[Y/N]" yn
        case $yn in
            [Yy]* ) install_php ${php_ver}
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
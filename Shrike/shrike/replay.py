#!/usr/bin/env python3

"""Execute the PHP interpreter on a script in the exact same manner as is done
when solving. This eliminates any heap layout changes that result from
differences in command line lengths or file descriptor allocations, or anything
else that would be problematic.
"""

import pathlib
import sys
import subprocess

DISABLE_FUNCTIONS_INI = (
        'disable_functions = "apache_child_terminate, apache_setenv, '
        'define_syslog_variables, escapeshellarg, escapeshellcmd, eval, '
        'exec, fp, fput, ftp_connect, ftp_exec, ftp_get, ftp_login, '
        'ftp_nb_fput, ftp_put, ftp_raw, ftp_rawlist, highlight_file, '
        'ini_alter, ini_get_all, ini_restore, inject_code, mysql_pconnect, '
        'openlog, passthru, php_uname, phpAds_remoteInfo, phpAds_XmlRpc, '
        'phpAds_xmlrpcDecode, phpAds_xmlrpcEncode, popen, posix_getpwuid, '
        'posix_kill, posix_mkfifo, posix_setpgid, posix_setsid, posix_setuid, '
        'posix_setuid, posix_uname, proc_close, proc_get_status, proc_nice, '
        'proc_open, proc_terminate, shell_exec, syslog, system, '
        'xmlrpc_entity_decode, fopen, glob, mkdir, fsockopen, tempnam,'
        'stream_socket_server"')

php = sys.argv[1]
fpath = pathlib.Path(sys.argv[2])

p = subprocess.run(
        [php, '-d', DISABLE_FUNCTIONS_INI, fpath.as_posix()],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=5)

print("Return code: {}".format(p.returncode))
print("[---- stdout ----]")
print(p.stdout)
print("[----------------]")
print("[---- stderr ----]")
print(p.stderr)
print("[----------------]")

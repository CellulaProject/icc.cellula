from icc.cellula.indexer.interfaces import IIndexer
from zope.interface import implementer, Interface
from zope.component import getUtility
import subprocess as sp
#import MySQLdb
#import cymysql
#import oursql
import pymysql
from icc.contentstorage import intdigest, hexdigest
import os.path, os

INDEX_TEMPLATE="""
index rt
{
    type = rt
    path = %(dir)s
    rt_field = title
    rt_field = content
    rt_attr_uint = text_id
}

searchd
{
	#listen			= 127.0.0.1:9312
	#listen			= %(dir)s/searchd.sock
	#listen			= 9312
	listen			= 127.0.0.1:9386:mysql41

	# log file, searchd run info is logged here
	# optional, default is 'searchd.log'
	log			= %(dir)s/searchd.log

	# query log file, all search queries are logged here
	# optional, default is empty (do not log queries)
	query_log		= %(dir)s/query.log

	# client read timeout, seconds
	# optional, default is 5
	read_timeout		= 5

	# request timeout, seconds
	# optional, default is 5 minutes
	client_timeout		= 300

	# maximum amount of children to fork (concurrent searches to run)
	# optional, default is 0 (unlimited)
	max_children		= 30

	# maximum amount of persistent connections from this master to each agent host
	# optional, but necessary if you use agent_persistent. It is reasonable to set the value
	# as max_children, or less on the agent's hosts.
	persistent_connections_limit	= 30

	# PID file, searchd process ID file name
	# mandatory
	pid_file		= %(dir)s/searchd.pid

	# seamless rotate, prevents rotate stalls if precaching huge datasets
	# optional, default is 1
	seamless_rotate		= 1

	# whether to forcibly preopen all indexes on startup
	# optional, default is 1 (preopen everything)
	preopen_indexes		= 1

	# whether to unlink .old index copies on succesful rotation.
	# optional, default is 1 (do unlink)
	unlink_old		= 1

	# attribute updates periodic flush timeout, seconds
	# updates will be automatically dumped to disk this frequently
	# optional, default is 0 (disable periodic flush)
	#
	# attr_flush_period	= 900


	# MVA updates pool size
	# shared between all instances of searchd, disables attr flushes!
	# optional, default size is 1M
	mva_updates_pool	= 1M

	# max allowed network packet size
	# limits both query packets from clients, and responses from agents
	# optional, default size is 8M
	max_packet_size		= 8M

	# max allowed per-query filter count
	# optional, default is 256
	max_filters		= 256

	# max allowed per-filter values count
	# optional, default is 4096
	max_filter_values	= 4096


	# socket listen queue length
	# optional, default is 5
	#
	# listen_backlog		= 5


	# per-keyword read buffer size
	# optional, default is 256K
	#
	# read_buffer		= 256K


	# unhinted read size (currently used when reading hits)
	# optional, default is 32K
	#
	# read_unhinted		= 32K


	# max allowed per-batch query count (aka multi-query count)
	# optional, default is 32
	max_batch_queries	= 32


	# max common subtree document cache size, per-query
	# optional, default is 0 (disable subtree optimization)
	#
	# subtree_docs_cache	= 4M


	# max common subtree hit cache size, per-query
	# optional, default is 0 (disable subtree optimization)
	#
	# subtree_hits_cache	= 8M


	# multi-processing mode (MPM)
	# known values are none, fork, prefork, and threads
	# threads is required for RT backend to work
	# optional, default is threads
	workers			= threads # for RT to work


	# max threads to create for searching local parts of a distributed index
	# optional, default is 0, which means disable multi-threaded searching
	# should work with all MPMs (ie. does NOT require workers=threads)
	#
	# dist_threads		= 4


	# binlog files path; use empty string to disable binlog
	# optional, default is build-time configured data directory
	#
	# binlog_path		= # disable logging
	binlog_path		= %(dir)s # binlog.001 etc will be created there


	# binlog flush/sync mode
	# 0 means flush and sync every second
	# 1 means flush and sync every transaction
	# 2 means flush every transaction, sync every second
	# optional, default is 2
	#
	# binlog_flush		= 2


	# binlog per-file size limit
	# optional, default is 128M, 0 means no limit
	#
	# binlog_max_log_size	= 256M


	# per-thread stack size, only affects workers=threads mode
	# optional, default is 64K
	#
	# thread_stack			= 128K


	# per-keyword expansion limit (for dict=keywords prefix searches)
	# optional, default is 0 (no limit)
	#
	# expansion_limit		= 1000


	# RT RAM chunks flush period
	# optional, default is 0 (no periodic flush)
	#
	# rt_flush_period		= 900


	# query log file format
	# optional, known values are plain and sphinxql, default is plain
	#
	# query_log_format		= sphinxql


	# version string returned to MySQL network protocol clients
	# optional, default is empty (use Sphinx version)
	#
	# mysql_version_string	= 5.0.37


	# default server-wide collation
	# optional, default is libc_ci
	#
	# collation_server		= utf8_general_ci


	# server-wide locale for libc based collations
	# optional, default is C
	#
	# collation_libc_locale	= ru_RU.UTF-8


	# threaded server watchdog (only used in workers=threads mode)
	# optional, values are 0 and 1, default is 1 (watchdog on)
	#
	# watchdog				= 1


	# costs for max_predicted_time model, in (imaginary) nanoseconds
	# optional, default is "doc=64, hit=48, skip=2048, match=64"
	#
	# predicted_time_costs	= doc=64, hit=48, skip=2048, match=64


	# current SphinxQL state (uservars etc) serialization path
	# optional, default is none (do not serialize SphinxQL state)
	#
	# sphinxql_state			= sphinxvars.sql


	# maximum RT merge thread IO calls per second, and per-call IO size
	# useful for throttling (the background) OPTIMIZE INDEX impact
	# optional, default is 0 (unlimited)
	#
	# rt_merge_iops			= 40
	# rt_merge_maxiosize		= 1M


	# interval between agent mirror pings, in milliseconds
	# 0 means disable pings
	# optional, default is 1000
	#
	# ha_ping_interval		= 0


	# agent mirror statistics window size, in seconds
	# stats older than the window size (karma) are retired
	# that is, they will not affect master choice of agents in any way
	# optional, default is 60 seconds
	#
	# ha_period_karma			= 60


	# delay between preforked children restarts on rotation, in milliseconds
	# optional, default is 0 (no delay)
	#
	# prefork_rotation_throttle	= 100


	# a prefix to prepend to the local file names when creating snippets
	# with load_files and/or load_files_scatter options
	# optional, default is empty
	#
	# snippets_file_prefix		= /mnt/common/server1/
}

#############################################################################
## common settings
#############################################################################

common
{

	# lemmatizer dictionaries base path
	# optional, defaut is /usr/local/share (see ./configure --datadir)
	#
	# lemmatizer_base = /usr/local/share/sphinx/dicts


	# how to handle syntax errors in JSON attributes
	# known values are 'ignore_attr' and 'fail_index'
	# optional, default is 'ignore_attr'
	#
	# on_json_attr_error = fail_index


	# whether to auto-convert numeric values from strings in JSON attributes
	# with auto-conversion, string value with actually numeric data
	# (as in {"key":"12345"}) gets stored as a number, rather than string
	# optional, allowed values are 0 and 1, default is 0 (do not convert)
	#
	# json_autoconv_numbers = 1


	# whether and how to auto-convert key names in JSON attributes
	# known value is 'lowercase'
	# optional, default is unspecified (do nothing)
	#
	# json_autoconv_keynames = lowercase


	# path to RLP root directory
	# optional, defaut is /usr/local/share (see ./configure --datadir)
	#
	# rlp_root = /usr/local/share/sphinx/rlp


	# path to RLP environment file
	# optional, defaut is /usr/local/share/rlp-environment.xml (see ./configure --datadir)
	#
	# rlp_environment = /usr/local/share/sphinx/rlp/rlp/etc/rlp-environment.xml


	# maximum total size of documents batched before processing them by the RLP
	# optional, default is 51200
	#
	# rlp_max_batch_size = 100k


	# maximum number of documents batched before processing them by the RLP
	# optional, default is 50
	#
	# rlp_max_batch_docs = 100


	# trusted plugin directory
	# optional, default is empty (disable UDFs)
	#
	# plugin_dir			= /usr/local/sphinx/lib

}

"""

@implementer(IIndexer)
class SphinxIndexer(object):
    executable="sphinx-searchd"
    def __init__(self):
        """Creates index service.
        1. Generates a config in conf_dir;
        2. Starts daemon tracking its pid pid_file;
        3. Hopefully stops daemon on application exit.
        """

        config=getUtility(Interface, "configuration")
        ic=config['indexer']
        self.data_dir=ic['data_dir']
        self.pid_file=ic['pid_file']
        self.conf_file=ic['conf_file']
        self.batch_amount=int(ic['batch_amount'])
        self.execpathname=self.run(self.executable, executable='which').strip()
        self.connection=None
        self.started=False
        self.test()
        self.create_config()
        self.start_daemon()

    def test(self):
        out=self.run('--help', executable=self.execpathname)
        if not out.startswith("Sphinx"):
            raise RuntimeError("cannot start Sphinx index server")

    def run(self, *params, ignore_err=False, executable=None):
        """Run extract binary and capture its stdout.
        If there is some stderr output, raise exception if
        it is not igored (ignore_err).
        """

        if executable == None:
            executable = self.execpathname

        exec_bundle=[executable]+list(params)
        # print ("------------>", exec_bundle)
        cp=sp.run(exec_bundle, stdout=sp.PIPE, stderr=sp.PIPE)
        if cp.stderr and not ignore_err:
            raise RuntimeError(cp.stderr.decode('utf-8').strip())
        return cp.stdout.decode('utf-8')


    def create_config(self):
        """Creates config file, controlling indexer.
        """

        config=INDEX_TEMPLATE % {"dir":self.data_dir}
        self.filepath_conf=os.path.join(self.data_dir, self.conf_file)
        of=open(self.filepath_conf, "w")
        of.write(config)
        of.close()

    def start_daemon(self):
        if self.started:
            return
        self.filepath_pid=os.path.join(self.data_dir, self.pid_file)
        # out=self.run('--pidfile', self.filepath_pid, '--config', self.filepath_conf)
        out=self.run('--config', self.filepath_conf)
        # print (out)
        # print (self.pid)
        self.started=True
        # self.connection=MySQLdb.connect(host="127.0.0.1", port=9386)
        # self.connection=cymysql.connect(host="127.0.0.1", port=9386)
        # self.connection=oursql.connect(host="127.0.0.1", port=9386)
        self.connection=pymysql.connect(host="127.0.0.1", port=9386, charset='utf8')

    @property
    def pid(self):
        return int(open(self.filepath_pid).read().strip())

    def __del__(self):
        if self.connection != None:
            self.connection.close()
        os.remove(self.filepath_conf)
        #pid=self.pid()
        self.run('--stopwait')
        #os.remove(self.filename_pid)

    def put(self, content, fields):
        print (fields.get('title', ''))
        content_id=intdigest(fields['id'])
        text_id=intdigest(fields['text-id'])
        title=fields.get('title', '')
        cursor=self.connection.cursor()
        content=self.clean(content)
        title=self.clean(title)

        title="Заголовок"
        content="Тело"

        print (content_id, title, content, text_id)
        cursor.execute(
            'INSERT INTO rt VALUES ( %s, %s, %s, %s) $end ;',
            (content_id, title, content, text_id)
        )

    def clean(self, s):
        return s.replace("'",' ').replace('"',' ').replace('\\', ' ')

    def search(self, query):
        cursor=self.connection.cursor()
        cursor.execute(
            "SELECT * FROM rt WHERE MATCH(%s);",
            (query,)
        )
        rc = cursor.fetchmay(self.batch_amount)
        rc = [[hexdigest(r[0])] + r[1:] for r in rc]
        return rc

    def remove(self, content_id):
        cursor.execute(
            "DELETE FROM rt WHERE id=%s;",
            (bindigest(content_id),)
        )
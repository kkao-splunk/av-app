# $SPLUNK_HOME/etc/apps/av-app/bin/input.py

'''
Modular Input Script

Copyright (C) 2012 Splunk, Inc.
All Rights Reserved

'''

import sys,logging,os,time,re,threading
import xml.dom.minidom
import tokens
from datetime import datetime

SPLUNK_HOME = os.environ.get("SPLUNK_HOME")


RESPONSE_HANDLER_INSTANCE = None
SPLUNK_PORT = 8089
STANZA = None
SESSION_TOKEN = None
REGEX_PATTERN = None

#dynamically load in any eggs in /etc/apps/snmp_ta/bin
EGG_DIR = SPLUNK_HOME + "/etc/apps/av-app/bin/"

for filename in os.listdir(EGG_DIR):
    if filename.endswith(".egg"):
        sys.path.append(EGG_DIR + filename)

import requests,json
from requests.auth import HTTPBasicAuth
from requests.auth import HTTPDigestAuth
from requests_oauthlib import OAuth1
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import WebApplicationClient
from requests.auth import AuthBase
from splunklib.client import connect
from splunklib.client import Service
from croniter import croniter


#set up logging
logging.root
logging.root.setLevel(logging.ERROR)
formatter = logging.Formatter('%(levelname)s %(message)s')
#with zero args , should go to STD ERR
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logging.root.addHandler(handler)

SCHEME = """<scheme>
    <title>Avanti</title>
    <description>REST API input for polling data from RESTful endpoints</description>
    <use_external_validation>true</use_external_validation>
    <streaming_mode>xml</streaming_mode>
    <use_single_instance>false</use_single_instance>

    <endpoint>
        <args>
            <arg name="name">
                <title>REST input name</title>
                <description>Name of this REST input</description>
            </arg>

            <arg name="endpoint">
                <title>Endpoint</title>
                <description>IP address + Port to request from: ex. 127.0.0.1:8080</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>true</required_on_create>
            </arg>

        </args>
    </endpoint>
</scheme>
"""

def get_current_datetime_for_cron():
    current_dt = datetime.now()
    #dont need seconds/micros for cron
    current_dt = current_dt.replace(second=0, microsecond=0)
    return current_dt

def do_validate():
    config = get_validation_config()
    print 'something'
    #if error , print_validation_error & sys.exit(2)

def do_run(config,endpoint_list):

    #setup some globals
    server_uri = config.get("server_uri")
    global SPLUNK_PORT
    global STANZA
    global SESSION_TOKEN
    global delimiter
    SPLUNK_PORT = server_uri[18:]
    STANZA = config.get("name")
    SESSION_TOKEN = config.get("session_key")

    #params
    http_method=config.get("http_method","GET")
    request_payload=config.get("request_payload")

    #none | basic | digest | oauth1 | oauth2
    auth_type=config.get("auth_type","none")

    #Delimiter to use for any multi "key=value" field inputs
    delimiter=config.get("delimiter",",")

    #for basic and digest
    auth_user=config.get("auth_user")
    auth_password=config.get("auth_password")

    #for oauth1
    oauth1_client_key=config.get("oauth1_client_key")
    oauth1_client_secret=config.get("oauth1_client_secret")
    oauth1_access_token=config.get("oauth1_access_token")
    oauth1_access_token_secret=config.get("oauth1_access_token_secret")

    #for oauth2
    oauth2_token_type=config.get("oauth2_token_type","Bearer")
    oauth2_access_token=config.get("oauth2_access_token")

    oauth2_refresh_token=config.get("oauth2_refresh_token")
    oauth2_refresh_url=config.get("oauth2_refresh_url")
    oauth2_refresh_props_str=config.get("oauth2_refresh_props")
    oauth2_client_id=config.get("oauth2_client_id")
    oauth2_client_secret=config.get("oauth2_client_secret")
    print 'hi'
    oauth2_refresh_props={}
    if not oauth2_refresh_props_str is None:
        oauth2_refresh_props = dict((k.strip(), v.strip()) for k,v in
              (item.split('=',1) for item in oauth2_refresh_props_str.split(delimiter)))
    oauth2_refresh_props['client_id'] = oauth2_client_id
    oauth2_refresh_props['client_secret'] = oauth2_client_secret

    http_header_propertys={}
    http_header_propertys_str=config.get("http_header_propertys")
    if not http_header_propertys_str is None:
        http_header_propertys = dict((k.strip(), v.strip()) for k,v in
              (item.split('=',1) for item in http_header_propertys_str.split(delimiter)))

    url_args={}
    url_args_str=config.get("url_args")
    if not url_args_str is None:
        url_args = dict((k.strip(), v.strip()) for k,v in
              (item.split('=',1) for item in url_args_str.split(delimiter)))

    #json | xml | text
    response_type=config.get("response_type","text")

    streaming_request=int(config.get("streaming_request",0))

    http_proxy=config.get("http_proxy")
    https_proxy=config.get("https_proxy")

    proxies={}

    if not http_proxy is None:
        proxies["http"] = http_proxy
    if not https_proxy is None:
        proxies["https"] = https_proxy

    cookies={}
    cookies_str=config.get("cookies")
    if not cookies_str is None:
        cookies = dict((k.strip(), v.strip()) for k,v in
              (item.split('=',1) for item in cookies_str.split(delimiter)))

    request_timeout=int(config.get("request_timeout",30))

    backoff_time=int(config.get("backoff_time",10))

    sequential_stagger_time  = int(config.get("sequential_stagger_time",0))

    polling_interval_string = config.get("polling_interval","60")

    if polling_interval_string.isdigit():
        polling_type = 'interval'
        polling_interval=int(polling_interval_string)
    else:
        polling_type = 'cron'
        cron_start_date = datetime.now()
        cron_iter = croniter(polling_interval_string, cron_start_date)

    index_error_response_codes=int(config.get("index_error_response_codes",0))

    response_filter_pattern=config.get("response_filter_pattern")

    if response_filter_pattern:
        global REGEX_PATTERN
        REGEX_PATTERN = re.compile(response_filter_pattern)

    response_handler_args={}
    response_handler_args_str=config.get("response_handler_args")
    if not response_handler_args_str is None:
        response_handler_args = dict((k.strip(), v.strip()) for k,v in
              (item.split('=',1) for item in response_handler_args_str.split(delimiter)))

    response_handler=config.get("response_handler","DefaultResponseHandler")
    module = __import__("responsehandlers")
    class_ = getattr(module,response_handler)

    global RESPONSE_HANDLER_INSTANCE
    RESPONSE_HANDLER_INSTANCE = class_(**response_handler_args)

    custom_auth_handler=config.get("custom_auth_handler")

    if custom_auth_handler:
        module = __import__("authhandlers")
        class_ = getattr(module,custom_auth_handler)
        custom_auth_handler_args={}
        custom_auth_handler_args_str=config.get("custom_auth_handler_args")
        if not custom_auth_handler_args_str is None:
            custom_auth_handler_args = dict((k.strip(), v.strip()) for k,v in (item.split('=',1) for item in custom_auth_handler_args_str.split(delimiter)))
        CUSTOM_AUTH_HANDLER_INSTANCE = class_(**custom_auth_handler_args)


    try:
        auth=None
        oauth2=None

        req_args = {"verify" : False ,"stream" : bool(streaming_request) , "timeout" : float(request_timeout)}

        if auth:
            req_args["auth"]= auth
        if url_args:
            req_args["params"]= url_args
        if cookies:
            req_args["cookies"]= cookies
        if http_header_propertys:
            req_args["headers"]= http_header_propertys
        if proxies:
            req_args["proxies"]= proxies
        if request_payload and not http_method == "GET":
            req_args["data"]= request_payload


        while True:

            if polling_type == 'cron':
                next_cron_firing = cron_iter.get_next(datetime)
                while get_current_datetime_for_cron() != next_cron_firing:
                    time.sleep(float(10))

            for endpoint in endpoint_list:

                if "params" in req_args:
                    req_args_params_current = dictParameterToStringFormat(req_args["params"])
                else:
                    req_args_params_current = ""
                if "cookies" in req_args:
                    req_args_cookies_current = dictParameterToStringFormat(req_args["cookies"])
                else:
                    req_args_cookies_current = ""
                if "headers" in req_args:
                    req_args_headers_current = dictParameterToStringFormat(req_args["headers"])
                else:
                    req_args_headers_current = ""
                if "data" in req_args:
                    req_args_data_current = req_args["data"]
                else:
                    req_args_data_current = ""

                try:

                    if True:
                        if http_method == "GET":
                            r = requests.get(endpoint,**req_args)
                        elif http_method == "POST":
                            r = requests.post(endpoint,**req_args)
                        elif http_method == "PUT":
                            r = requests.put(endpoint,**req_args)

                except requests.exceptions.Timeout,e:
                    logging.error("HTTP Request Timeout error: %s" % str(e))
                    time.sleep(float(backoff_time))
                    continue
                except Exception as e:
                    logging.error("Exception performing request: %s" % str(e))
                    time.sleep(float(backoff_time))
                    continue
                try:
                    r.raise_for_status()
                    if streaming_request:
                        for line in r.iter_lines():
                            if line:
                                logging.debug(line);
                                handle_output(r,line,response_type,req_args,endpoint)
                    else:
                        handle_output(r,r.text,response_type,req_args,endpoint)
                except requests.exceptions.HTTPError,e:
                    error_output = r.text
                    error_http_code = r.status_code
                    if index_error_response_codes:
                        error_event=""
                        error_event += 'http_error_code = %s error_message = %s' % (error_http_code, error_output)
                        print_xml_single_instance_mode(error_event)
                        sys.stdout.flush()
                    logging.error("HTTP Request error: %s" % str(e))
                    time.sleep(float(backoff_time))
                    continue


                if "data" in req_args:
                    checkParamUpdated(req_args_data_current,req_args["data"],"request_payload")
                if "params" in req_args:
                    checkParamUpdated(req_args_params_current,dictParameterToStringFormat(req_args["params"]),"url_args")
                if "headers" in req_args:
                    checkParamUpdated(req_args_headers_current,dictParameterToStringFormat(req_args["headers"]),"http_header_propertys")
                if "cookies" in req_args:
                    checkParamUpdated(req_args_cookies_current,dictParameterToStringFormat(req_args["cookies"]),"cookies")

                if sequential_stagger_time > 0:
                    time.sleep(float(sequential_stagger_time))

            if polling_type == 'interval':
                time.sleep(float(polling_interval))

    except RuntimeError,e:
        logging.error("Looks like an error: %s" % str(e))
        sys.exit(2)


def replaceTokens(raw_string):

    try:
        url_list = [raw_string]
        substitution_tokens = re.findall("\$(?:\w+)\$",raw_string)
        for token in substitution_tokens:
            token_response = getattr(tokens,token[1:-1])()
            if(isinstance(token_response,list)):
                temp_list = []
                for token_response_value in token_response:
                    for url in url_list:
                        temp_list.append(url.replace(token,token_response_value))
                url_list = temp_list
            else:
                for index,url in enumerate(url_list):
                    url_list[index] = url.replace(token,token_response)
        return url_list
    except:
        e = sys.exc_info()[1]
        logging.error("Looks like an error substituting tokens: %s" % str(e))


def checkParamUpdated(cached,current,rest_name):

    if not (cached == current):
        try:
            args = {'host':'localhost','port':SPLUNK_PORT,'token':SESSION_TOKEN}
            service = Service(**args)
            item = service.inputs.__getitem__(STANZA[7:])
            item.update(**{rest_name:current})
        except RuntimeError,e:
            logging.error("Looks like an error updating the modular input parameter %s: %s" % (rest_name,str(e),))


def dictParameterToStringFormat(parameter):

    if parameter:
        return ''.join(('{}={}'+delimiter).format(key, val) for key, val in parameter.items())[:-1]
    else:
        return None



def handle_output(response,output,type,req_args,endpoint):

    try:
        if REGEX_PATTERN:
            search_result = REGEX_PATTERN.search(output)
            if search_result == None:
                return
        RESPONSE_HANDLER_INSTANCE(response,output,type,req_args,endpoint)
        sys.stdout.flush()
    except RuntimeError,e:
        logging.error("Looks like an error handle the response output: %s" % str(e))

# prints validation error data to be consumed by Splunk
def print_validation_error(s):
    print "<error><message>%s</message></error>" % encodeXMLText(s)

# prints XML stream
def print_xml_single_instance_mode(s):
    print "<stream><event><data>%s</data></event></stream>" % encodeXMLText(s)

# prints simple stream
def print_simple(s):
    print "%s\n" % s

def encodeXMLText(text):
    text = text.replace("&", "&amp;")
    text = text.replace("\"", "&quot;")
    text = text.replace("'", "&apos;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text

def usage():
    print "usage: %s [--scheme|--validate-arguments]"
    logging.error("Incorrect Program Usage")
    sys.exit(2)

def do_scheme():
    print SCHEME

#read XML configuration passed from splunkd, need to refactor to support single instance mode
def get_input_config():
    config = {}

    try:
        # read everything from stdin

        config_str = sys.stdin.read()

        # parse the config XML
        doc = xml.dom.minidom.parseString(config_str)
        root = doc.documentElement

        session_key_node = root.getElementsByTagName("session_key")[0]
        if session_key_node and session_key_node.firstChild and session_key_node.firstChild.nodeType == session_key_node.firstChild.TEXT_NODE:
            data = session_key_node.firstChild.data
            config["session_key"] = data

        server_uri_node = root.getElementsByTagName("server_uri")[0]
        if server_uri_node and server_uri_node.firstChild and server_uri_node.firstChild.nodeType == server_uri_node.firstChild.TEXT_NODE:
            r = requests.get('https://127.0.0.1:8089/servicesNS/Nobody/av-app/storage/collections/data/token',verify=False,auth=('admin','changeme'))
            token = str(r.json()[0]['accessId'])
            data = data + '/avanti/v0.3/ListClusters?provider=aws&region=us-west-1'
            data = data + '&access_token=' + token
            config["server_uri"] = data

        conf_node = root.getElementsByTagName("configuration")[0]
        if conf_node:
            logging.debug("XML: found configuration")
            stanza = conf_node.getElementsByTagName("stanza")[0]
            if stanza:
                stanza_name = stanza.getAttribute("name")
                if stanza_name:
                    logging.debug("XML: found stanza " + stanza_name)
                    config["name"] = stanza_name

                    params = stanza.getElementsByTagName("param")
                    for param in params:
                        param_name = param.getAttribute("name")
                        logging.debug("XML: found param '%s'" % param_name)
                        if param_name and param.firstChild and param.firstChild.nodeType == param.firstChild.TEXT_NODE:
                            data = param.firstChild.data
                            data = str(data)
                            data = 'http://' + data
                            r = requests.get('https://127.0.0.1:8089/servicesNS/Nobody/av-app/storage/collections/data/token',verify=False,auth=('admin','changeme'))
                            token = str(r.json()[0]['accessId'])
                            data = data + '/avanti/v0.3/ListClusters?provider=aws&region=us-west-1'
                            data = data + '&access_token=' + token

                            config[param_name] = data
                            logging.debug("XML: '%s' -> '%s'" % (param_name, data))

        checkpnt_node = root.getElementsByTagName("checkpoint_dir")[0]
        if checkpnt_node and checkpnt_node.firstChild and \
           checkpnt_node.firstChild.nodeType == checkpnt_node.firstChild.TEXT_NODE:
            config["checkpoint_dir"] = checkpnt_node.firstChild.data

        if not config:
            raise Exception, "Invalid configuration received from Splunk."


    except Exception, e:
        raise Exception, "Error getting Splunk configuration via STDIN: %s" % str(e)

    return config

#read XML configuration passed from splunkd, need to refactor to support single instance mode
def get_validation_config():
    val_data = {}
    # read everything from stdin
    val_str = sys.stdin.read()

    # parse the validation XML
    doc = xml.dom.minidom.parseString(val_str)
    root = doc.documentElement

    print "XML: found items"
    item_node = root.getElementsByTagName("item")[0]
    if item_node:
        print "XML: found item"

        name = item_node.getAttribute("name")
        val_data["stanza"] = name

        params_node = item_node.getElementsByTagName("param")
        for param in params_node:
            name = param.getAttribute("name")
            print "Found param %s" % name
            if name and param.firstChild and \
               param.firstChild.nodeType == param.firstChild.TEXT_NODE:
                val_data[name] = param.firstChild.data

    return val_data

if __name__ == '__main__':

    if len(sys.argv) > 1:
        if sys.argv[1] == "--scheme":
            do_scheme()
        elif sys.argv[1] == "--validate-arguments":
            do_validate()
        else:
            usage()
    else:
        print 'sigh'
        config = get_input_config()
        original_endpoint=config.get("endpoint")
        #token replacement
        endpoint_list = replaceTokens(original_endpoint)

        sequential_mode=int(config.get("sequential_mode",0))

        if bool(sequential_mode):
            do_run(config,endpoint_list)
        else:  #parallel mode
            for endpoint in endpoint_list:
                requester = threading.Thread(target=do_run, args=(config,[endpoint]))
                requester.start()

    sys.exit(0)

import http.client as httplib
import urllib.parse as urllib
from difflib import SequenceMatcher
import string
import random
import argparse
import cgi
import glob
import importlib.util as imp
import xml.etree.ElementTree as ET

########################################
part1 = '''<!DOCTYPE html><html><head><meta charset="utf-8" /><title>Burpy Version - 0.1 Test Report</title><link href="http://www.w3resource.com/twitter-bootstrap/twitter-bootstrap-v2/docs/assets/css/bootstrap.css" rel="stylesheet" type="text/css" /></head><body><div class="well span12 offset1"><h1>Burpy v0.1 Report</h1></br><p><b>Author </b>: <a href="http://www.debasish.in/">Debasish Mandal</a></p><p><b>Total Number of Request(s) Tested </b>: {number}</br><b>Scan Scope : </b>{target}</br></div><div class="well span12 offset1"><div class="container-fluid"><div class="accordion" id="accordion2"></div>'''
part2 = '''<div class="accordion-group"><div class="accordion-heading"><a class="accordion-toggle" data-toggle="collapse" data-parent="#accordion2" href="#{col_id}">{title}</a></div><div id="{col_id}" class="accordion-body collapse" style="height: 0px; "><div class="accordion-inner">{response}</div></div></div>'''
part3 = '''</div></div></div><script type="text/javascript" src="http://www.w3resource.com/twitter-bootstrap/twitter-bootstrap-v2/docs/assets/js/jquery.js"></script><script type="text/javascript" src="http://www.w3resource.com/twitter-bootstrap/twitter-bootstrap-v2/docs/assets/js/bootstrap-collapse.js"></script></body></html>'''

class Core:
    '''
    This class holds the core components of Burpy
    '''
    def banner(self):
        '''
        Print this banner on start up.
        '''
        print('''
             ____		                                  ___  __ 
            |  _ \                                           / _ \/_ |
            | |_) |_   _ _ __ _ __  _   _   ______  __   __ | | | || |
            |  _ <| | | | '__| '_ \| | | | |______| \ \ / / | | | || |
            | |_) | |_| | |  | |_) | |_| |           \ V /  | |_| || |
            |____/ \__,_|_|  | .__/ \__, |            \_/    \___(_)_|
                         | |     __/ |                            
                         |_|    |___/      		
        ''')
        print('                  Burpy v0.1 Portable and Flexible Web Application Security Scanner')
        print('                        Author : Debasish Mandal (http://www.debasish.in)')

    def cmd_option(self):
        '''
        Parse Options
        '''
        global target_domain
        global burp_suite_log
        global ssl
        parser = argparse.ArgumentParser()
        parser.add_argument('-t', type=str, help='Target/Scan Scope domain - Its mandatory option', dest='target_domain')
        parser.add_argument('-l', type=str, help='Full path to burp suite log - Its mandatory option', dest='burp_suite_log')
        parser.add_argument('-s', type=str, help='Use of SSL on or off - Its mandatory option', dest='SSL')
        opts = parser.parse_args()
        burp_suite_log = opts.burp_suite_log
        target_domain = opts.target_domain
        ssl = opts.SSL
        mandatories = ['target_domain', 'burp_suite_log', 'SSL']
        for m in mandatories:
            if not getattr(opts, m):
                print("[+] Error!! You have missed a mandatory option\n")
                parser.print_help()
                exit(-1)

    def id_generator(self, size=6, chars=string.ascii_uppercase + string.digits):
        '''
        Generate random string.
        this Random String function copied from :-> http://stackoverflow.com/questions/2257441/python-random-string-generation-with-upper-case-letters-and-digits
        '''
        return ''.join(random.choice(chars) for x in range(size))

    def write_report(self, title, res_reason, res_code, base_request, crafted_request, res_head_dict, latest_response):
        '''
        When any test result is positive, Use this routine to write the raw request to html report.Cud not make it more simple.
        '''
        latest_response = cgi.escape(latest_response)
        base_request = base_request.replace('\n', '</br>')
        crafted_request = crafted_request.replace('\n', '</br>')
        HOST = target_domain
        url = self.gerequestinfo(base_request, "path")
        if len(url) > 50:
            path_u = url[:50] + "..."
        else:
            path_u = url
        raw_resp = "HTTP/1.1 " + str(res_reason) + " " + res_code + "</br>"
        for ele in res_head_dict:
            raw_resp += ele + ": " + res_head_dict[ele] + "</br>"
        raw_resp += "</br>" + latest_response
        try:
            raw = "<b>Base Request</b></br>" + base_request + "</br></br><b>Crafted Request&nbsp;&nbsp;&nbsp;[" + title[1] + "]</b></br></br>" + crafted_request + "</br><b>Live Response</b></br>" + raw_resp
        except Exception as e:
            raw += "<b>One Exception Occurred while parsing the response..</b>"
        with open('Report.html', 'a') as report:
            final = part2.replace('{response}', raw).replace('{col_id}', self.id_generator()).replace('{title}', "<b>http(s)://" + HOST + path_u + "</b>[" + title[0] + "]")  # Exactly I don't have any idea why I'm using random number to locate bootstrap collapse, but it's 2.30 AM and I gotta complete this code today
            try:
                report.write(final)
            except Exception as e:
                print('[+] Just handled one Unicode conversion Error. In Some cases it')
        report.close()

    def difference(self, cont1, cont2):
        '''
        Simple function to Compute diff percentage of two data sets.
        '''
        m = SequenceMatcher(None, cont1, cont2)
        return m.ratio() * 100

    def parse_log(self, log_path):
        '''
        This function accepts burp log file path.
        and returns a dict. of request and response
        result = {'GET /page.php...':'200 OK HTTP / 1.1....','':'',.....}
        '''
        result = {}
        try:
            with open(log_path):
                pass
        except IOError:
            print("[+] Error!!! ", log_path, "doesn't exist..")
            exit()
        try:
            tree = ET.parse(log_path)
        except Exception as e:
            print('[+] Oops..!Please make sure binary data is not present in Log')
            exit()
        root = tree.getroot()
        for reqs in root.findall('item'):
            raw_req = reqs.find('request').text
            raw_req = urllib.unquote(raw_req).decode('utf8')
            raw_resp = reqs.find('response').text
            result[raw_req] = raw_resp
        return result

    def gerequestinfo(self, raw_stream, query):
        headers = {}
        sp = raw_stream.split('\n\n', 1)
        if len(sp) > 1:
            head = sp[0]
            body = sp[1]
        else:
            head = sp[0]
            body = ""
        c1 = head.split('\n', head.count('\n'))
        method = c1[0].split(' ', 2)[0]
        path = c1[0].split(' ', 2)[1]
        if query == "path":
            return path
        for i in range(1, head.count('\n')+1):
            slice1 = c1[i].split(': ', 1)
            if slice1[0] != "":
                headers[slice1[0]] = slice1[1]
        return headers[query]

    def loadallmodules(self):
        avlbl_mods = {}
        mods = glob.glob("modules/*.py")
        for mod in mods:
            print('[+] \t\tLoaded...', mod)
            try:
                modl = imp.load_source('main', mod)
                avlbl_mods[self.id_generator()] = modl.main
            except Exception as e:
                print('[+] Error!! Could not import ', mod)
        return avlbl_mods

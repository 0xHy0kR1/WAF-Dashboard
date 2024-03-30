import xml.etree.ElementTree as ET
from burpy.rawweb import RawWeb
import urllib.parse as urllib
import base64
import csv
log_path = 'burp_crawl3.log'
output_log = 'crawl3_log.csv'
class_flag = "1"

class LogParse:
    def __init__(self):
        pass
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
            raw_req = urllib.unquote(raw_req)
            raw_resp = reqs.find('response').text
            result[raw_req] = raw_resp
        return result

    def parseRawHTTPReq(self, rawReq):
        try:
            raw = rawReq.decode('utf8')
        except Exception as e:
            raw = rawReq
        global headers,method,body,path
        headers = {}
        sp = raw.split('\n\n', 1)
        if len(sp) > 1:
            head = sp[0]
            body = sp[1]
        else:
            head = sp[0]
            body = ""
        c1 = head.split('\n', head.count('\n'))
        method = c1[0].split(' ', 2)[0]
        if len(c1[0].split(' ', 2)) >= 2:
            path = c1[0].split(' ', 2)[1]
        else:
            path = ""
        for i in range(1, head.count('\n')+1):
            slice1 = c1[i].split(': ', 1)
            if slice1[0] != "":
                headers[slice1[0]] = slice1[1]
        return headers, method, body, path

badwords = ['sleep', 'drop', 'uid', 'select', 'waitfor', 'delay', 'system', 'union', 'order by', 'group by']
def ExtractKeywords(method, path_enc, body_enc, headers):
    badwords_count = 0
    path = urllib.unquote_plus(path_enc)
    body = urllib.unquote(body_enc)
    single_q = path.count("'") + body.count("'")
    double_q = path.count("\"") + body.count("\"")
    dashes = path.count("--") + body.count("--")
    braces = path.count("(") + body.count("(")
    spaces = path.count(" ") + body.count(" ")

    for word in badwords:
        badwords_count += path.count(word) + body.count(word)
        
    for header in headers:
        badwords_count += headers[header].count(word) + headers[header].count(word)

    return [method, path_enc.encode('utf-8').strip(), body_enc.encode('utf-8').strip(), single_q, double_q, dashes, braces, spaces, badwords_count, class_flag]
    input('>>>')

# Open the log file
with open(output_log, 'w') as csvfile:
    c = csv.writer(csvfile)
    c.writerow(["method", "path", "body", "single_q", "double_q", "dashes", "braces", "spaces", "badwords", "class"])

obj = LogParse()
result = obj.parse_log(log_path)
for items in result:
    data = []
    try:
        decoded_request = base64.b64decode(items).decode('utf-8')  # Try decoding as UTF-8
        lines = decoded_request.split('\r\n')  # Split the request into lines
        parsed_request = '\n'.join(lines)  # Join the lines into a single string
        headers, method, body, path = obj.parseRawHTTPReq(parsed_request)  # Pass the single string to the function
        result = ExtractKeywords(method, path, body, headers)
        with open(output_log, "a") as csvfile:
            c = csv.writer(csvfile)
            c.writerow(result)

    except UnicodeDecodeError:
        print("[+] Error decoding request data: UnicodeDecodeError")
import xml.etree.ElementTree as ET
from burpy.rawweb import RawWeb
import urllib.parse as urllib
import base64
import csv
log_path = 'burp.log'
output_log = 'httplog.csv'
def parse_log(log_path):
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

def parseRawHTTPReq(rawReq):
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

# Open the log file
with open(output_log, 'w') as csvfile:
    c = csv.writer(csvfile)
    c.writerow(["method", "body", "path", "headers"])

result = parse_log(log_path)
for items in result:
    data = []
    try:
        decoded_request = base64.b64decode(items).decode('utf-8')  # Try decoding as UTF-8
        lines = decoded_request.split('\r\n')  # Split the request into lines
        parsed_request = '\n'.join(lines)  # Join the lines into a single string
        headers, method, body, path = parseRawHTTPReq(parsed_request)  # Pass the single string to the function
        data.append(method)
        data.append(body)
        data.append(path)
        data.append(headers)
        with open(output_log, 'a') as csvfile:
            c = csv.writer(csvfile)
            c.writerow(data)

    except UnicodeDecodeError:
        print("[+] Error decoding request data: UnicodeDecodeError")
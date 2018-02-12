'''
Created on Feb 10, 2018

@author: Larry
'''
import json
import time
import urllib.parse
import urllib.request

#Google Maps timezone API key 
# from project: API-key-maps-timezone
# https://console.developers.google.com/apis/credentials?project=python-poc-dev1-1518307432680
#
# API-key-maps-timezone
# AIzaSyBICrTYV1LCkFtOmE25TBlzsRPuE-EfeYg
#
# API key 2
# AIzaSyBwzU5Af6igToW5cZwr5gx75Pqsw7Z8T6s
#
# https://maps.googleapis.com/maps/api/timezone/json?location=38.908133,-77.047119&timestamp=1458000000&key=YOUR_API_KEY
#
# https://developers.google.com/maps/documentation/timezone/start
#
#
#




def main():
    tz = timezone(39.6034810, -119.6822510, 1331161200)
    print ('Timezone:', tz)
    
    tz = timezone(38.908133, -77.047119, 1458000000)
    print ('Timezone:', tz)
    
    

def timezone(lat, lng, timestamp):
    # The maps_key defined below isn't a valid Google Maps API key.
    # You need to get your own API key.
    # See https://developers.google.com/maps/documentation/timezone/get-api-key
    # maps_key = 'YOUR_KEY_HERE'
    maps_key = 'AIzaSyBICrTYV1LCkFtOmE25TBlzsRPuE-EfeYg'
    timezone_base_url = 'https://maps.googleapis.com/maps/api/timezone/json'

    # This joins the parts of the URL together into one string.
    url = timezone_base_url + '?' + urllib.parse.urlencode(
        {'location': "%s,%s" % (lat, lng),
        'timestamp': timestamp,
        'key': maps_key, }
    )

    current_delay = 0.1  # Set the initial retry delay to 100ms.
    max_delay = 3600  # Set the maximum retry delay to 1 hour.

    while True:
        try:
            headers = {}
            #headers["Accept"]  = "application/json; charset=utf-8"

            req = urllib.request.Request(url, headers=headers)
            
            
            #req.add_header("Accept", "application/json; charset=utf-8")
            
            # Get the API response.
            # response = str(urllib2.urlopen(url).read())
            # x = urllib.request.urlopen(url).read()
            # response = str(urllib.request.urlopen(url).read())
              
            #response = str(req.urlopen(url).read())
            #response = response.replace('\\n', '').replace(' ', '')
            
            resp = urllib.request.urlopen(req)
            resp_data = resp.read()
            
        except IOError:
            pass  # Fall through to the retry loop.
        else:
            # If we didn't get an IOError then parse the result.
            # note this fails, apparently py has problem with stack?
            #result = json.loads(response.replace('\\n', ''))
            
            #jt = '{ "a": 1, "b": "two"}'
            #result = json.loads(jt)   
                   
            #result = json.loads(response)
            result = json.loads(resp_data)

            if result['status'] == 'OK':
                return result['timeZoneId']
            
            elif result['status'] != 'UNKNOWN_ERROR':
                
                # Many API errors cannot be fixed by a retry, e.g. INVALID_REQUEST or
                # ZERO_RESULTS. There is no point retrying these requests.
                raise Exception(result['error_message'])

        if current_delay > max_delay:
            raise Exception('Too many retry attempts.')
        
        print( 'Waiting', current_delay, 'seconds before retrying.')
        time.sleep(current_delay)
        current_delay *= 2  # Increase the delay each time we retry.

#tz = timezone(39.6034810, -119.6822510, 1331161200)
#print ('Timezone:', tz)
  
    
if __name__ == '__main__':
    main()

    
    
'''
import base64
import urllib.request

request = urllib.request.Request('http://mysite/admin/index.cgi?index=127')
base64string =  bytes('%s:%s' % ('login', 'password'), 'ascii')
request.add_header("Authorization", "Basic %s" % base64string)
result = urllib.request.urlopen(request)
resulttext = result.read()


'''    
    
    
       
# Import the re library to support regular expressions
import re
import pathlib
import csv

# The AnaPyzerAnalyzer class contains all methods that are used to process information into a displayable form
# from logs created by AnaPyzerParser object methods.


class AnaPyzerAnalyzer:
    def __init__(self):
        self._known_ips = {}

    @staticmethod
    def malicious_activity_report(parsed_log):
        ip_address_log_info_dict = {}
        # Goes through parsed log and puts a list lists timestamps(datetime)
        # and urls into a dictionary with the relevant ip as the key
        for entry in range(0, parsed_log['length']):
            log_entry_ip = parsed_log[entry][parsed_log['client-ip']]
            if log_entry_ip in ip_address_log_info_dict:
                ip_address_log_info_dict[log_entry_ip]['timestamps'].append(parsed_log[entry][parsed_log['date']] + parsed_log[entry][parsed_log['timestamp']])
                ip_address_log_info_dict[log_entry_ip]['urls'].append(parsed_log[entry][parsed_log['uri-stem']])
            else:
                ip_address_log_info_dict[log_entry_ip] = {
                    'timestamps': [parsed_log[entry][parsed_log['date']] + parsed_log[entry][parsed_log['timestamp']]],
                    'urls': [parsed_log[entry][parsed_log['uri-stem']]]
                }
        # initializes report output variable
        report_output = ""

        # loops through each ip in the dictionary and performs calculations on the relvant timestamps and urls
        for ip in ip_address_log_info_dict:
            # initialize variables needed for calculations
            malicious = False
            attempts = 1
            counter = 0
            current_timestamp = 0
            current_url = 1
            current_index = 0
            timestamps = ip_address_log_info_dict[ip]['timestamps']
            urls = ip_address_log_info_dict[ip]['urls']
            # loops through timestamps and converts eacn timestamp to a numerical value
            for timestamp in timestamps:
                temp = ""
                for c in timestamp:
                    if c.isdigit():
                        temp += c
                timestamps[current_index] = temp
                current_index += 1
            timestamps.sort()
            urls.sort()
            url_attempts = []
            # loops through urls and checks if the same url has been accessed more than 5 times by one ip
            # If so sets boolean variable malicious to true
            for url in urls:
                try:
                    if url == urls[current_url]:
                        attempts += 1
                        current_url += 1
                        if attempts > 5 and url not in url_attempts:
                            url_attempts.append(url)
                            malicious = True
                    else:
                        current_url += 1
                        attempts = 1

                except IndexError:
                    break
                current_index = 0
            # loops through timestamps and performs calculations to determine if a malicious attempt has been made
            for timestamp in timestamps:
                # go forward looking for timestamps within 1 secs
                if (int(timestamp) - int(timestamps[current_timestamp])) < 1:
                    counter += 1
                else:
                    current_timestamp = current_index
                    counter = 0
                    # go backward looking for timestamps within 1 secs
                    for i in range(1, 10):
                        try:
                            if (int(timestamps[current_timestamp]) - int(timestamps[current_timestamp - i])) < 1:
                                counter += 1
                        except IndexError:
                            break
                # if website has been accessed 5 or more times and malicious is set to true,
                # adds ip and relevant urls accessed to report_output
                if counter >= 5 and malicious:
                    report_output += "Malicious activity detected from " + ip + ":\n"
                    for url in url_attempts:
                        if url != "/":
                            report_output += url + "  was accessed more than five times within one second by " + ip + "\n"
                    malicious = False
                    report_output += "\n"
                current_index += 1;
        return report_output

    # get_connections_per_hour takes in a log parsed by the above parse_w3c_tolist method
    # and returns a list containing how many unique ip connections were present during each hour of the day
    # this parsed list can be used with the plot_hourly_connections method
    @staticmethod
    def get_connections_per_hour(parsed_log):
        connections_per_hour_table = {}
        print(parsed_log)
        if parsed_log is None:
            return None

        i = 0
        date = parsed_log[i][parsed_log['date']]
        connections_per_hour_table[date] = {}
        while i < parsed_log['length']:
            # iterate through the ip addresses recorded
            if parsed_log[i][parsed_log['date']] != date:
                date = parsed_log[i][parsed_log['date']]
                connections_per_hour_table[date] = {}

            time_string = str(parsed_log[i][parsed_log['timestamp']])
            user_ip_address = str(parsed_log[i][parsed_log['client-ip']])
            hours = time_string[:2]

            if connections_per_hour_table[date].get(hours):
                connections_per_hour_table[date][hours] += [user_ip_address]
            else:
                connections_per_hour_table[date][hours] = [user_ip_address]

            i += 1

        for date in connections_per_hour_table:
            for time in connections_per_hour_table[date]:
                ip_count = len(set(connections_per_hour_table[date][time]))
                connections_per_hour_table[date][time] = ip_count

        connections_per_hour_table['xlabel'] = "Hour of Day"
        connections_per_hour_table['ylabel'] = "Unique IPs Recorded"
        connections_per_hour_table['title'] = "Connections Per Hour"
        return connections_per_hour_table

    # The plot_connections method take a log formatted by the get_connections_per_hour method
    @staticmethod
    def announce_connections(connections_log):
        for date in connections_log:
            print(date)
            for log in connections_log[date]:
                print(str(connections_log[date][log]) + " unique connections found at " + log + ":00")

    @staticmethod
    def get_connection_length_report(parsed_log):

        ip_connection_time = {}
        i = 0
        connection_time = 0
        current_ip = ''

        while i < parsed_log['length']:

            # Check that the IP address hasn't changed
            if current_ip == parsed_log[i][parsed_log['client-ip']]:
                connection_time += 1

            else:
                if i > 0:
                    connection_time += 1
                    ip_end_time = parsed_log[i - 1][parsed_log['timestamp']]
                    info_array = [connection_time, ip_end_time]

                    if ip_connection_time.get(current_ip):
                        ip_connection_time[current_ip].append(info_array)

                    else:
                        ip_connection_time[current_ip] = [info_array]

                current_ip = parsed_log[i][parsed_log['client-ip']]

                # reset connection_time if ip has changed
                connection_time = 0

            i += 1
        output = ""
        for ip in ip_connection_time:
            # time_sum = 0  Dan unused variable
            for info in ip_connection_time[ip]:
                output += "IP Address: " + ip + ": " + str(info[0]) + " request(s) " + " at: " + str(info[1]) + "\n\n"

        return output


    def _lookup_ipv4(self, ip):

        ip_split = ip.split(".")
        try:
            ip_1 = int(ip_split[0])
            ip_2 = int(ip_split[1])
            ip_3 = int(ip_split[2])
            ip_4 = int(ip_split[3])
        except ValueError:
            self._known_ips[ip] = "INV"
            return None

        if ip_1 > 255 or ip_1 < 0:
            self._known_ips[ip] = "INV"
            return None
        if ip_2 > 255 or ip_2 < 0:
            self._known_ips[ip] = "INV"
            return None
        if ip_3 > 255 or ip_3 < 0:
            self._known_ips[ip] = "INV"
            return None
        if ip_4 > 255 or ip_4 < 0:
            self._known_ips[ip] = "INV"
            return None

        if self._known_ips.get(ip):
            return self._known_ips[ip]
        else:
            filename = 'ips/ipv4' + str(ip_1) + ".csv"

            try:
                with open(filename, 'r') as ip_db:
                    reader = csv.reader(ip_db)
                    ipv4 = list(reader)
            except:
                if ip_1 >= 225:
                    return "ZZ"
                else:
                    return "INV"
            ip_db.close()

            # format of each line =
            # [0] = starting limit ip_1 [1] = starting limit ip_2 [2] = starting limit ip_3  [3] =starting limit ip_4
            # [4] = ending limit ip_1   [5] = ending limit ip_2   [6] = ending limit ip_3    [7] = ending limit ip_4
            # [8]= Country Code

            i = 0
            # if the starting ip has a number less than the ending ip
            # the entire range of ips starting with ip_1 belongs to the country code in [8]

            if int(ipv4[i][0]) <= ip_1 and int(ipv4[i][4]) > ip_1:
                self._known_ips[ip] = ipv4[i][8]
                return ipv4[i][8]

            while i < len(ipv4):
                if int(ipv4[i][1]) <= ip_2 and int(ipv4[i][5]) > ip_2:
                    self._known_ips[ip] = ipv4[i][8]
                    return ipv4[i][8]

                if int(ipv4[i][2]) <= ip_3 and int(ipv4[i][6]) > ip_3:
                    self._known_ips[ip] = ipv4[i][8]
                    return ipv4[i][8]

                if int(ipv4[i][3]) <= ip_4 and int(ipv4[i][7]) > ip_4:
                    self._known_ips[ip] = ipv4[i][8]
                    return ipv4[i][8]
                i += 1
            # Just in case something doesn't work out, provide a default case of 'unknown'
            self._known_ips[ip] = "INV"
            return "INV"

    def ip_connection_report(self, parsed_log):
        ip_connections = {}

        i = 0
        date = parsed_log[i][parsed_log['date']]
        ip_connections[date] = {}
        # iterate through data of each date recorded
        while i < parsed_log['length']:
            # iterate through the ip addresses recorded
            if parsed_log[i][parsed_log['date']] != date:
                date = parsed_log[i][parsed_log['date']]
                ip_connections[date] = {}

            user_ip_address = str(parsed_log[i][parsed_log['client-ip']])

            if ip_connections[date].get(user_ip_address):
                ip_connections[date][user_ip_address] += 1
            else:
                ip_connections[date][user_ip_address] = 1
            i += 1
        cc_report = {}
        for date in ip_connections:
            cc_report[date] = {}
            for ip_address in ip_connections[date]:
                ip_country_code = self._lookup_ipv4(ip_address)
                if ip_country_code is not None:
                    if cc_report[date].get(ip_country_code):
                        cc_report[date][ip_country_code] += 1
                    else:
                        cc_report[date][ip_country_code] = 1

        cc_report['xlabel'] = "Country Code"
        cc_report['ylabel'] = "Unique Connections"
        cc_report['title'] = "Connections by Country"

        return cc_report
    
    # get_web_pages takes in a log parsed by parse_w3c_tolist method
    @staticmethod
    def get_web_pages(parsed_log):
        web_page_dictionary = {}
        web_page_bytes = {}

        for entry in range(0, parsed_log['length']):
            url = parsed_log[entry][parsed_log['uri-stem']]
            # print("resource " + url)
            bytes_received = parsed_log[entry][parsed_log['bytes-received']]
            # print("sent " + bytes_sent)
            #referrer = parsed_log[entry][parsed_log['referrer']]
            #print("referrer : " + referrer)
            if url in web_page_dictionary:
                web_page_dictionary[url] += 1
                web_page_bytes[url] += int(bytes_received)
            else:
                web_page_dictionary[url] = 1
                web_page_bytes[url] = int(bytes_received)
                website_report = "Web Site Resource Report has " + str(len(web_page_dictionary)) + " entries \n\n "
                website_report += "The top 50 resources are : \n\n"

        # for url, count in web_page_dictionary.items():
        i = 1
        for url,count in sorted(web_page_dictionary.items(),key = lambda t:t[1], reverse=True):
            website_report += "Web Site resource: " + url + " was hit " + str(count) + " times \n"
            i += 1
            if i > 50:
                break
        return website_report

    @classmethod
    def write_parsed_log_to_csv(cls, parsed_log, out_file):
        for line in range(0, parsed_log['length']):
            line_data = parsed_log[line]
            out_line = ""
            for i in range(0, len(line_data)):
                if i < len(line_data) - 1:
                    if ',' in line_data[i]:
                        out_line += '"' + line_data[i] + '"' + ","
                    else:
                        out_line += line_data[i] + ","
            out_file.write(out_line + '\n')
        return True

    @classmethod
    def save_report_to_file(cls, in_data, out_file):
        for line in in_data:
            out_file.write(line + '\n')
        return True

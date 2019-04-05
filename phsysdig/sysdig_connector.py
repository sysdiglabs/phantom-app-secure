# -----------------------------------------
# Phantom sample App Connector python file
# -----------------------------------------

# Phantom App imports
import phantom.app as phantom
from phantom.base_connector import BaseConnector
from phantom.action_result import ActionResult

# Usage of the consts file is recommended
# from sysdig_consts import *
import requests
import json
import time
import os
import tempfile
import base64

from kubernetes_client import KubernetesClient
from sdcclient import SdSecureClient, SdMonitorClient


class RetVal(tuple):
    def __new__(cls, val1, val2=None):
        return tuple.__new__(RetVal, (val1, val2))


class SysdigConnector(BaseConnector):

    def __init__(self):

        # Call the BaseConnectors init first
        super(SysdigConnector, self).__init__()

        self._state = None

        self._duration_in_seconds = None
        self._kubernetes_config = None
        self._sysdig_api_token = None
        self._sysdig_api_endpoint = None

        self._kubernetes_client = None
        self._sysdig_client = None

    def _handle_start_capture(self, param):

        # Implement the handler here
        # use self.save_progress(...) to send progress messages back to the platform
        self.save_progress("In action handler for: {0}".format(self.get_action_identifier()))

        # Add an action result object to self (BaseConnector) to represent the action for this param
        action_result = self.add_action_result(ActionResult(dict(param)))

        # Access action parameters passed in the 'param' dictionary
        pod_name = param['pod_name']
        event_time = int(time.time())
        job_name = 'sysdig-{}-{}'.format(pod_name, event_time)

        hostname = self._kubernetes_client.find_node_running_pod(pod_name)
        hostname = hostname.split(".")[0]
        ok, data = self._sysdig_client.create_sysdig_capture(hostname=hostname, capture_name=job_name,
                                                            duration=self._duration_in_seconds, capture_filter=None)

        if not ok:
            raise Exception(data)

        # Add the response into the data section
        # action_result.add_data(response)

        # Add a dictionary that is made up of the most important values from data into the summary
        # summary = action_result.update_summary({})
        # summary['num_data'] = len(action_result['data'])

        # Return success, no need to set the message, only the status
        # BaseConnector will create a textual message based off of the summary dictionary
        return action_result.set_status(phantom.APP_SUCCESS)

    def handle_action(self, param):

        ret_val = phantom.APP_SUCCESS

        # Get the action that we are supposed to execute for this App Run
        action_id = self.get_action_identifier()

        self.debug_print("action_id", self.get_action_identifier())

        if action_id == 'start_capture':
            ret_val = self._handle_start_capture(param)

        return ret_val

    def initialize(self):

        # Load the state in initialize, use it to store data
        # that needs to be accessed across actions
        self._state = self.load_state()

        # get the asset config
        config = self.get_config()

        self._duration_in_seconds = config['duration_in_seconds']
        self._kubernetes_config = config['kubernetes_config']
        self._sysdig_api_token = config['sysdig_api_token']
        self._sysdig_api_endpoint = config['sysdig_api_endpoint']

        kubernetes_config = tempfile.NamedTemporaryFile(delete=False)
        kubernetes_config.write(base64.b64decode(self._kubernetes_config))
        kubernetes_config.close()

        self._kubernetes_client = KubernetesClient(kubernetes_config.name)
        self._sysdig_client = SdSecureClient(token=self._sysdig_api_token, sdc_url=self._sysdig_api_endpoint)

        os.remove(kubernetes_config.name)

        return phantom.APP_SUCCESS

    def finalize(self):

        # Save the state, this data is saved accross actions and app upgrades
        self.save_state(self._state)
        return phantom.APP_SUCCESS


if __name__ == '__main__':

    import pudb
    import argparse

    pudb.set_trace()

    argparser = argparse.ArgumentParser()

    argparser.add_argument('input_test_json', help='Input Test JSON file')
    argparser.add_argument('-u', '--username', help='username', required=False)
    argparser.add_argument('-p', '--password', help='password', required=False)

    args = argparser.parse_args()
    session_id = None

    username = args.username
    password = args.password

    if (username is not None and password is None):

        # User specified a username but not a password, so ask
        import getpass
        password = getpass.getpass("Password: ")

    if (username and password):
        try:
            print ("Accessing the Login page")
            r = requests.get("https://127.0.0.1/login", verify=False)
            csrftoken = r.cookies['csrftoken']

            data = dict()
            data['username'] = username
            data['password'] = password
            data['csrfmiddlewaretoken'] = csrftoken

            headers = dict()
            headers['Cookie'] = 'csrftoken=' + csrftoken
            headers['Referer'] = 'https://127.0.0.1/login'

            print ("Logging into Platform to get the session id")
            r2 = requests.post("https://127.0.0.1/login", verify=False, data=data, headers=headers)
            session_id = r2.cookies['sessionid']
        except Exception as e:
            print ("Unable to get session id from the platfrom. Error: " + str(e))
            exit(1)

    with open(args.input_test_json) as f:
        in_json = f.read()
        in_json = json.loads(in_json)
        print(json.dumps(in_json, indent=4))

        connector = SysdigConnector()
        connector.print_progress_message = True

        if (session_id is not None):
            in_json['user_session_token'] = session_id
            connector._set_csrf_info(csrftoken, headers['Referer'])

        ret_val = connector._handle_action(json.dumps(in_json), None)
        print (json.dumps(json.loads(ret_val), indent=4))

    exit(0)

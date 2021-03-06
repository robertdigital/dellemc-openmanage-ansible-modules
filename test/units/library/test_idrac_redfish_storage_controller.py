# -*- coding: utf-8 -*-

#
# Dell EMC OpenManage Ansible Modules
# Version 2.1
# Copyright (C) 2019 Dell Inc.

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# All rights reserved. Dell, EMC, and other trademarks are trademarks of Dell Inc. or its subsidiaries.
# Other trademarks may be trademarks of their respective owners.
#

from __future__ import absolute_import

import pytest
from ansible.modules.remote_management.dellemc import idrac_redfish_storage_controller
from units.modules.remote_management.dellemc.common import FakeAnsibleModule, Constants
from units.compat.mock import MagicMock
from units.modules.remote_management.dellemc.common import AnsibleFailJSonException
from ansible.module_utils.six.moves.urllib.error import URLError, HTTPError
from ansible.module_utils.urls import ConnectionError, SSLValidationError

@pytest.fixture
def idrac_connection_mock_for_redfish_storage_controller(mocker, redfish_response_mock):
    connection_class_mock = mocker.patch('ansible.modules.remote_management.dellemc.idrac_redfish_storage_controller.Redfish')
    idrac_redfish_connection_mock_obj = connection_class_mock.return_value.__enter__.return_value
    idrac_redfish_connection_mock_obj.invoke_request.return_value = redfish_response_mock
    return idrac_redfish_connection_mock_obj


class TestIdracRedfishStorageController(FakeAnsibleModule):
    module = idrac_redfish_storage_controller

    msg = "All of the following: key, key_id and old_key are required for ReKey operation."
    @pytest.mark.parametrize("input",
                             [{"param": {"command": "ReKey", "mode": "LKM", "key_id": "myid"}, "msg": msg},
                              {"param": {"command": "ReKey", "mode": "LKM", "old_key": "mykey"}, "msg": msg},
                              {"param": {"command": "ReKey", "mode": "LKM", "key": "mykey"}, "msg": msg}
                              ])
    def test_validate_inputs_error_case_01(self, input):
        f_module = self.get_module_mock(params=input["param"])
        with pytest.raises(Exception) as exc:
            self.module.validate_inputs(f_module)
        assert exc.value.args[0] == input["msg"]

    @pytest.mark.parametrize("input", [{"controller_id": "c1"}])
    def test_check_encryption_capability_failure(self, idrac_connection_mock_for_redfish_storage_controller,
                                                 redfish_response_mock, input):
        f_module = self.get_module_mock(params=input)
        msg = "Encryption is not supported on the storage controller: c1"
        redfish_response_mock.success = True
        redfish_response_mock.json_data = {'Oem':{'Dell':{'DellController':{'SecurityStatus':"EncryptionNotCapable"}}}}
        with pytest.raises(Exception) as exc:
            self.module.check_encryption_capability(f_module, idrac_connection_mock_for_redfish_storage_controller)
        assert exc.value.args[0] == msg

    def test_check_raid_service(self, idrac_connection_mock_for_redfish_storage_controller,
                                redfish_response_mock):
        f_module = self.get_module_mock()
        msg = "Installed version of iDRAC does not support this feature using Redfish API"
        redfish_response_mock.success = False
        with pytest.raises(Exception) as exc:
            self.module.check_raid_service(f_module, idrac_connection_mock_for_redfish_storage_controller)
        assert exc.value.args[0] == msg

    msg = "Installed version of iDRAC does not support this feature using Redfish API"
    @pytest.mark.parametrize("input",
                             [
                                 # {"error": HTTPError('http://testhost.com', 400, msg, {}, None),"msg": msg},
                                 {"error": URLError("test"), "msg": "<urlopen error test>"}
                             ])
    def test_check_raid_service_exceptions(self, idrac_connection_mock_for_redfish_storage_controller, input):
        f_module = self.get_module_mock(params=input)
        idrac_connection_mock_for_redfish_storage_controller.invoke_request.side_effect = input["error"]
        with pytest.raises(Exception) as exc:
            self.module.check_raid_service(f_module, idrac_connection_mock_for_redfish_storage_controller)
        assert exc.value.args[0] == input['msg']

    @pytest.mark.parametrize("input", [{"volume_id": ["v1"]}])
    def test_check_volume_array_exists(self, idrac_connection_mock_for_redfish_storage_controller,
                                       redfish_response_mock, input):
        f_module = self.get_module_mock(params=input)
        msg = "Unable to locate the virtual disk with the ID: v1"
        redfish_response_mock.success = False
        with pytest.raises(Exception) as exc:
            self.module.check_volume_array_exists(f_module,
                                                  idrac_connection_mock_for_redfish_storage_controller)
        assert exc.value.args[0] == msg

    @pytest.mark.parametrize("input", [{"item": "x1"}])
    def test_check_id_exists(self,
                             idrac_connection_mock_for_redfish_storage_controller,
                             redfish_response_mock, input):
        f_module = self.get_module_mock(params=input)
        msg = "item with id x1 not found in system"
        redfish_response_mock.success = False
        with pytest.raises(Exception) as exc:
            self.module.check_id_exists(f_module,
                                        idrac_connection_mock_for_redfish_storage_controller,
                                        "item", "uri")
        assert exc.value.args[0] == msg

    arg_list1 = [{"command": "ResetConfig", "controller_id": "c1"},
                 {"command": "RemoveControllerKey", "controller_id": "c1"},
                 {"command": "ReKey", "controller_id": "c1"},
                 {"command": "SetControllerKey", "controller_id": "c1", "key": "key", "key_id": "key_id"},
                 {"command": "AssignSpare", "target": "target"}]

    @pytest.mark.parametrize("param", arg_list1)
    def test_idrac_redfish_storage_controller_main_success_case_01(self,
                                                                   mocker,
                                                                   redfish_default_args,
                                                                   redfish_response_mock,
                                                                   idrac_connection_mock_for_redfish_storage_controller,
                                                                   param):
        mocker.patch('ansible.modules.remote_management.dellemc.idrac_redfish_storage_controller.validate_inputs')
        mocker.patch('ansible.modules.remote_management.dellemc.idrac_redfish_storage_controller.check_raid_service')
        mocker.patch('ansible.modules.remote_management.dellemc.idrac_redfish_storage_controller.check_id_exists'),
        mocker.patch('ansible.modules.remote_management.dellemc.idrac_redfish_storage_controller.check_volume_array_exists'),
        mocker.patch('ansible.modules.remote_management.dellemc.idrac_redfish_storage_controller.check_encryption_capability'),
        f_module = self.get_module_mock(params=param)
        redfish_response_mock.success = True
        redfish_response_mock.headers = {"Location" : "Jobs/1234"}
        redfish_default_args.update(param)
        result = self._run_module(redfish_default_args)
        assert result["changed"] is True
        assert result['msg'] == "Successfully submitted the job that performs the {0} operation".format(param["command"])
        assert result["task"]["id"] == "1234"
        assert result["task"]["uri"] == "Jobs/1234"
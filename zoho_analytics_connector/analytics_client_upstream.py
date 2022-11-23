# $Id$
from io import StringIO
import urllib
import json
import requests


class AnalyticsClient:
    """
    AnalyticsClient provides the python based language binding to the https based API of Zoho Analytics.
    """

    CLIENT_VERSION = "2.1.0"
    COMMON_ENCODE_CHAR = "UTF-8"

    def __init__(self, client_id, client_secret, refresh_token):
        """
        Creates a new C{AnalyticsClient} instance.
        @param client_id: User client id for OAUth
        @type client_id:string
        @param client_secret: User client secret for OAuth
        @type client_secret:string
        @param refresh_token: User's refresh token for OAUth).
        @type refresh_token:string
        """

        self.proxy = False
        self.proxy_host = None
        self.proxy_port = None
        self.proxy_user_name = None
        self.proxy_password = None

        self.accounts_server_url = "https://accounts.zoho.com"
        self.analytics_server_url = "https://analyticsapi.zoho.com"

        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.access_token = None

    def get_org_instance(self, org_id):
        """
        Returns a new C{OrgAPI} instance.
        @param org_id: The id of the organization.
        @type org_id:string
        """
        org_instance = AnalyticsClient.OrgAPI(self, org_id)
        return org_instance

    def get_workspace_instance(self, org_id, workspace_id):
        """
        Returns a new C{WorkspaceAPI} instance.
        @param org_id: The id of the organization.
        @type org_id:string
        @param workspace_id: The id of the workspace.
        @type workspace_id:string
        """
        workspace_instance = AnalyticsClient.WorkspaceAPI(self, org_id, workspace_id)
        return workspace_instance

    def get_view_instance(self, org_id, workspace_id, view_id):
        """
        Returns a new C{ViewAPI} instance.
        @param org_id: The id of the organization.
        @type org_id:string
        @param workspace_id: The id of the workspace.
        @type workspace_id:string
        @param view_id: The id of the view.
        @type view_id:string
        """
        view_instance = AnalyticsClient.ViewAPI(self, org_id, workspace_id, view_id)
        return view_instance

    def get_bulk_instance(self, org_id, workspace_id):
        """
        Returns a new C{BulkAPI} instance.
        @param org_id: The id of the organization.
        @type org_id:string
        @param workspace_id: The id of the workspace.
        @type workspace_id:string
        """
        data_instance = AnalyticsClient.BulkAPI(self, org_id, workspace_id)
        return data_instance

    def get_orgs(self):
        """
        Returns list of all accessible organizations.
        @return: Organization list.
        @rtype:list
        @raise ServerError: If the server has received the request but did not process the request
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        endpoint = "/restapi/v2/orgs"
        response = self.send_api_request("GET", endpoint, None, None)
        return response["data"]["orgs"]

    def get_workspaces(self):
        """
        Returns list of all accessible workspaces.
        @return: Workspace list.
        @rtype:list
        @raise ServerError: If the server has received the request but did not process the request
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        endpoint = "/restapi/v2/workspaces"
        response = self.send_api_request("GET", endpoint, None, None)
        return response["data"]

    def get_owned_workspaces(self):
        """
        Returns list of owned workspaces.
        @return: Workspace list.
        @rtype:list
        @raise ServerError: If the server has received the request but did not process the request
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        endpoint = "/restapi/v2/workspaces/owned"
        response = self.send_api_request("GET", endpoint, None, None)
        return response["data"]["workspaces"]

    def get_shared_workspaces(self):
        """
        Returns list of shared workspaces.
        @return: Workspace list.
        @rtype:list
        @raise ServerError: If the server has received the request but did not process the request
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        endpoint = "/restapi/v2/workspaces/shared"
        response = self.send_api_request("GET", endpoint, None, None)
        return response["data"]["workspaces"]

    def get_recent_views(self):
        """
        Returns list of recently accessed views.
        @return: View list.
        @rtype:list
        @raise ServerError: If the server has received the request but did not process the request
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        endpoint = "/restapi/v2/recentviews"
        response = self.send_api_request("GET", endpoint, None, None)
        return response["data"]["views"]

    def get_dashboards(self):
        """
        Returns list of all accessible dashboards.
        @return: Dashboard list.
        @rtype:list
        @raise ServerError: If the server has received the request but did not process the request
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        endpoint = "/restapi/v2/dashboards"
        response = self.send_api_request("GET", endpoint, None, None)
        return response["data"]

    def get_owned_dashboards(self):
        """
        Returns list of owned dashboards.
        @return: Dashboard list.
        @rtype:list
        @raise ServerError: If the server has received the request but did not process the request
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        endpoint = "/restapi/v2/dashboards/owned"
        response = self.send_api_request("GET", endpoint, None, None)
        return response["data"]["views"]

    def get_shared_dashboards(self):
        """
        Returns list of shared dashboards.
        @return: Dashboard list.
        @rtype:list
        @raise ServerError: If the server has received the request but did not process the request
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        endpoint = "/restapi/v2/dashboards/shared"
        response = self.send_api_request("GET", endpoint, None, None)
        return response["data"]["views"]

    def get_workspace_details(self, workspace_id):
        """
        Returns details of the specified workspace.
        @param workspace_id: Id of the workspace.
        @type workspace_id: string
        @raise ServerError: If the server has received the request but did not process the request due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        @return: Workspace details.
        @rtype:dictionary
        """
        endpoint = "/restapi/v2/workspaces/" + workspace_id
        response = self.send_api_request("GET", endpoint, None, None)
        return response["data"]["workspaces"]

    def get_view_details(self, view_id, config={}):
        """
        Returns details of the specified view.
        @param view_id: Id of the view.
        @type view_id: string
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @raise ServerError: If the server has received the request but did not process the request due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        @return: View details.
        @rtype:dictionary
        """
        endpoint = "/restapi/v2/views/" + view_id
        response = self.send_api_request("GET", endpoint, config, None)
        return response["data"]["views"]

    class OrgAPI:
        """
        OrgAPI contains organization level operations.
        """

        def __init__(self, ac, org_id):
            self.ac = ac
            self.request_headers = {}
            self.request_headers["ZANALYTICS-ORGID"] = org_id

        def create_workspace(self, workspace_name, config={}):
            """
            Create a blank workspace in the specified organization.
            @param workspace_name: The name of the workspace.
            @type workspace_name:string
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return: Created workspace id.
            @rtype:string
            """
            config["workspaceName"] = workspace_name
            endpoint = "/restapi/v2/workspaces/"
            response = self.ac.send_api_request("POST", endpoint, config, self.request_headers)
            return int(response["data"]["workspaceId"])

        def get_admins(self):
            """
            Returns list of admins for a specified organization.
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return: Organization admin list.
            @rtype:list
            """
            endpoint = "/restapi/v2/orgadmins"
            response = self.ac.send_api_request("GET", endpoint, None, self.request_headers)
            return response["data"]["orgAdmins"]

        def get_users(self):
            """
            Returns list of users for the specified organization.
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return: User list.
            @rtype:list
            """
            endpoint = "/restapi/v2/users"
            response = self.ac.send_api_request("GET", endpoint, None, self.request_headers)
            return response["data"]["users"]

        def add_users(self, email_ids, config={}):
            """
            Add users to the specified organization.
            @param email_ids: The email address of the users to be added.
            @type email_ids:list
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            config["emailIds"] = email_ids
            endpoint = "/restapi/v2/users"
            self.ac.send_api_request("POST", endpoint, config, self.request_headers)

        def remove_users(self, email_ids, config={}):
            """
            Remove users from the specified organization.
            @param email_ids: The email address of the users to be removed.
            @type email_ids:list
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            config["emailIds"] = email_ids
            endpoint = "/restapi/v2/users"
            self.ac.send_api_request("DELETE", endpoint, config, self.request_headers)

        def activate_users(self, email_ids, config={}):
            """
            Activate users in the specified organization.
            @param email_ids: The email address of the users to be activated.
            @type email_ids:list
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            config["emailIds"] = email_ids
            endpoint = "/restapi/v2/users/active"
            self.ac.send_api_request("PUT", endpoint, config, self.request_headers)

        def deactivate_users(self, email_ids, config={}):
            """
            Deactivate users in the specified organization.
            @param email_ids: The email address of the users to be deactivated.
            @type email_ids:list
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            config["emailIds"] = email_ids
            endpoint = "/restapi/v2/users/inactive"
            self.ac.send_api_request("PUT", endpoint, config, self.request_headers)

        def change_user_role(self, email_ids, role, config={}):
            """
            Change role for the specified users.
            @param email_ids: The email address of the users to be deactivated.
            @type email_ids:list
            @param role: New role for the users.
            @type role:string
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            config["emailIds"] = email_ids
            config["role"] = role
            endpoint = "/restapi/v2/users/role"
            self.ac.send_api_request("PUT", endpoint, config, self.request_headers)

        def get_subscription_details(self):
            """
            Returns subscription details of the specified organization.
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return: Subscription details.
            @rtype:dictionary
            """
            endpoint = "/restapi/v2/subscription"
            response = self.ac.send_api_request("GET", endpoint, None, self.request_headers)
            return response["data"]["subscription"]

        def get_meta_details(self, workspace_name, view_name):
            """
            Returns details of the specified workspace/view.
            @param workspace_name: Name of the workspace.
            @type workspace_name:string
            @param view_name: Name of the view.
            @type view_name:string
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return: Workspace (or) View meta details.
            @rtype:dictionary
            """
            config = {}
            config["workspaceName"] = workspace_name
            if view_name != None:
                config["viewName"] = view_name
            endpoint = "/restapi/v2/metadetails"
            response = self.ac.send_api_request("GET", endpoint, config, self.request_headers)
            return response["data"]

    class WorkspaceAPI:
        """
        WorkspaceAPI contains workspace level operations.
        """

        def __init__(self, ac, org_id, workspace_id):
            self.ac = ac
            self.endpoint = "/restapi/v2/workspaces/" + workspace_id
            self.request_headers = {}
            self.request_headers["ZANALYTICS-ORGID"] = org_id

        def copy(self, new_workspace_name, config={}, dest_org_id=None):
            """
            Copy the specified workspace from one organization to another or within the organization.
            @param new_workspace_name: Name of the new workspace.
            @type new_workspace_name: string
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @param dest_org_id: Id of the organization where the destination workspace is present. Can be C{None}.
            @type dest_org_id: string
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return: Copied workspace id.
            @rtype:string
            """
            config["newWorkspaceName"] = new_workspace_name
            headers = self.request_headers.copy()
            if bool(dest_org_id):
                headers["ZANALYTICS-DEST-ORGID"] = dest_org_id
            response = self.ac.send_api_request("POST", self.endpoint, config, headers)
            return int(response["data"]["workspaceId"])

        def rename(self, workspace_name, config={}):
            """
            Rename a specified workspace in the organization.
            @param workspace_name: New name for the workspace.
            @type workspace_name: string
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            config["workspaceName"] = workspace_name
            response = self.ac.send_api_request("PUT", self.endpoint, config, self.request_headers)

        def delete(self):
            """
            Delete a specified workspace in the organization.
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            response = self.ac.send_api_request("DELETE", self.endpoint, None, self.request_headers)

        def get_secret_key(self, config={}):
            """
            Returns the secret key of the specified workspace.
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return: Workspace secret key.
            @rtype:string
            """
            endpoint = self.endpoint + "/secretkey"
            response = self.ac.send_api_request("GET", endpoint, config, self.request_headers)
            return response["data"]["workspaceKey"]

        def add_favorite(self):
            """
            Adds a specified workspace as favorite.
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            endpoint = self.endpoint + "/favorite"
            response = self.ac.send_api_request("POST", endpoint, None, self.request_headers)

        def remove_favorite(self):
            """
            Remove a specified workspace from favorite.
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            endpoint = self.endpoint + "/favorite"
            response = self.ac.send_api_request("DELETE", endpoint, None, self.request_headers)

        def add_default(self):
            """
            Adds a specified workspace as default.
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            endpoint = self.endpoint + "/default"
            response = self.ac.send_api_request("POST", endpoint, None, self.request_headers)

        def remove_default(self):
            """
            Remove a specified workspace from default.
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            endpoint = self.endpoint + "/default"
            response = self.ac.send_api_request("DELETE", endpoint, None, self.request_headers)

        def get_admins(self):
            """
            Returns list of admins for the specified workspace.
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return: Workspace admin list.
            @rtype:list
            """
            endpoint = self.endpoint + "/admins"
            response = self.ac.send_api_request("GET", endpoint, None, self.request_headers)
            return response["data"]["workspaceAdmins"]

        def add_admins(self, email_ids, config={}):
            """
            Add admins for the specified workspace.
            @param email_ids: The email address of the admin users to be added.
            @type email_ids: list
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            config["emailIds"] = email_ids
            endpoint = self.endpoint + "/admins"
            self.ac.send_api_request("POST", endpoint, config, self.request_headers)

        def remove_admins(self, email_ids, config={}):
            """
            Remove admins from the specified workspace.
            @param email_ids: The email address of the admin users to be removed.
            @type email_ids: list
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            config["emailIds"] = email_ids
            endpoint = self.endpoint + "/admins"
            self.ac.send_api_request("DELETE", endpoint, config, self.request_headers)

        def get_share_info(self):
            """
            Returns shared details of the specified workspace.
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return: Workspace share info.
            @rtype:dictionary
            """
            endpoint = self.endpoint + "/share"
            response = self.ac.send_api_request("GET", endpoint, None, self.request_headers)
            return response["data"]

        def share_views(self, view_ids, email_ids, permissions, config={}):
            """
            Share views to the specified users.
            @param view_ids: View ids which to be shared.
            @type view_ids: list
            @param email_ids: The email address of the users to whom the views need to be shared.
            @type email_ids: list
            @param permissions: Contains permission details.
            @type permissions: dictionary
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            config["viewIds"] = view_ids
            config["emailIds"] = email_ids
            config["permissions"] = permissions
            endpoint = self.endpoint + "/share"
            self.ac.send_api_request("POST", endpoint, config, self.request_headers)

        def remove_share(self, view_ids, email_ids, config={}):
            """
            Remove shared views for the specified users.
            @param view_ids: View ids whose sharing needs to be removed.
            @type view_ids: list
            @param email_ids: The email address of the users to whom the sharing need to be removed.
            @type email_ids: list
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            config["emailIds"] = email_ids
            if view_ids != None:
                config["viewIds"] = view_ids
            endpoint = self.endpoint + "/share"
            self.ac.send_api_request("DELETE", endpoint, config, self.request_headers)

        def get_folders(self):
            """
            Returns list of all accessible folders for the specified workspace.
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return: Folder list.
            @rtype:list
            """
            endpoint = self.endpoint + "/folders"
            response = self.ac.send_api_request("GET", endpoint, None, self.request_headers)
            return response["data"]["folders"]

        def create_folder(self, folder_name, config={}):
            """
            Create a folder in the specified workspace.
            @param folder_name: Name of the folder to be created.
            @type folder_name: string
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return: Created folder id.
            @rtype:string
            """
            config["folderName"] = folder_name
            endpoint = self.endpoint + "/folders"
            response = self.ac.send_api_request("POST", endpoint, config, self.request_headers)
            return int(response["data"]["folderId"])

        def get_views(self, config={}):
            """
            Returns list of all accessible views for the specified workspace.
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return: View list.
            @rtype:list
            """
            endpoint = self.endpoint + "/views"
            response = self.ac.send_api_request("GET", endpoint, config, self.request_headers)
            return response["data"]["views"]

        def create_table(self, table_design):
            """
            Create a table in the specified workspace.
            @param table_design: Table structure.
            @type table_design: dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return: created table id.
            @rtype:string
            """
            config = {}
            config["tableDesign"] = table_design
            endpoint = self.endpoint + "/tables"
            response = self.ac.send_api_request("POST", endpoint, config, self.request_headers)
            return int(response["data"]["viewId"])

        def copy_views(self, view_ids, dest_workspace_id, config={}, dest_org_id=None):
            """
            Copy the specified views from one workspace to another workspace.
            @param view_ids: The id of the views to be copied.
            @type view_ids: list
            @param dest_workspace_id: The destination workspace id.
            @type dest_workspace_id: string
            @param dest_org_id: Id of the organization where the destination workspace is present. Can be C{None}.
            @type dest_org_id: string
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return: View list.
            @rtype:list
            """
            config["viewIds"] = view_ids
            config["destWorkspaceId"] = dest_workspace_id
            endpoint = self.endpoint + "/views/copy"
            headers = self.request_headers.copy()
            if bool(dest_org_id):
                headers["ZANALYTICS-DEST-ORGID"] = dest_org_id
            response = self.ac.send_api_request("POST", endpoint, config, headers)
            return response["data"]["views"]

        def enable_domain_access(self):
            """
            Enable workspace to the specified white label domain.
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            endpoint = self.endpoint + "/wlaccess"
            response = self.ac.send_api_request("POST", endpoint, None, self.request_headers)

        def disable_domain_access(self):
            """
            Disable workspace from the specified white label domain.
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            endpoint = self.endpoint + "/wlaccess"
            response = self.ac.send_api_request("DELETE", endpoint, None, self.request_headers)

        def rename_folder(self, folder_id, folder_name, config={}):
            """
            Rename a specified folder in the workspace.
            @param folder_id: Id of the folder.
            @type folder_id: string
            @param folder_name: New name for the folder.
            @type folder_name: string
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            config["folderName"] = folder_name
            endpoint = self.endpoint + "/folders/" + folder_id
            self.ac.send_api_request("PUT", endpoint, config, self.request_headers)

        def delete_folder(self, folder_id):
            """
            Delete a specified folder in the workspace.
            @param folder_id: Id of the folder to be deleted.
            @type folder_id: string
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            endpoint = self.endpoint + "/folders/" + folder_id
            self.ac.send_api_request("DELETE", endpoint, None, self.request_headers)

        def get_groups(self):
            """
            Returns list of groups for the specified workspace.
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return: Group list.
            @rtype:list
            """
            endpoint = self.endpoint + "/groups"
            response = self.ac.send_api_request("GET", endpoint, None, self.request_headers)
            return response["data"]["groups"]

        def create_group(self, group_name, email_ids, config={}):
            """
            Create a group in the specified workspace.
            @param group_name: Name of the group.
            @type group_name: string
            @param email_ids: The email address of the users to be added to the group.
            @type email_ids: list
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return: Created group id.
            @rtype:string
            """
            config["groupName"] = group_name
            config["emailIds"] = email_ids
            endpoint = self.endpoint + "/groups"
            response = self.ac.send_api_request("POST", endpoint, config, self.request_headers)
            return int(response["data"]["groupId"])

        def get_group_details(self, group_id):
            """
            Get the details of the specified group.
            @param group_id: Id of the group.
            @type group_id: string
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return: Details of the specified group.
            @rtype:dictionary
            """
            endpoint = self.endpoint + "/groups/" + group_id
            response = self.ac.send_api_request("GET", endpoint, None, self.request_headers)
            return response["data"]["groups"]

        def rename_group(self, group_id, group_name, config={}):
            """
            Rename a specified group.
            @param group_id: Id of the group.
            @type group_id: string
            @param group_name: New name for the group.
            @type group_name: string
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            config["groupName"] = group_name
            endpoint = self.endpoint + "/groups/" + group_id
            self.ac.send_api_request("PUT", endpoint, config, self.request_headers)

        def delete_group(self, group_id):
            """
            Delete a specified group.
            @param group_id: The id of the group.
            @type group_id: string
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            endpoint = self.endpoint + "/groups/" + group_id
            self.ac.send_api_request("DELETE", endpoint, None, self.request_headers)

        def add_group_members(self, group_id, email_ids, config={}):
            """
            Add users to the specified group.
            @param group_id: Id of the group.
            @type group_id: string
            @param email_ids: The email address of the users to be added to the group.
            @type email_ids: list
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            config["emailIds"] = email_ids
            endpoint = self.endpoint + "/groups/" + group_id + "/members"
            self.ac.send_api_request("POST", endpoint, config, self.request_headers)

        def remove_group_members(self, group_id, email_ids, config={}):
            """
            Remove users from the specified group.
            @param group_id: Id of the group.
            @type group_id: string
            @param email_ids: The email address of the users to be removed from the group.
            @type email_ids: list
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            config["emailIds"] = email_ids
            endpoint = self.endpoint + "/groups/" + group_id + "/members"
            self.ac.send_api_request("DELETE", endpoint, config, self.request_headers)

        def create_slideshow(self, slide_name, view_ids, config={}):
            """
            Create a slideshow in the specified workspace.
            @param slide_name: Name of the slideshow to be created.
            @type slide_name: string
            @param view_ids: Ids of the view to be included in the slideshow.
            @type view_ids: list
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return: Id of the created slideshow.
            @rtype:string
            """
            endpoint = self.endpoint + "/slides"
            config["slideName"] = slide_name
            config["viewIds"] = view_ids
            response = self.ac.send_api_request("POST", endpoint, config, self.request_headers)
            return int(response["data"]["slideId"])

        def update_slideshow(self, slide_id, config={}):
            """
            Update details of the specified slideshow.
            @param slide_id: The id of the slideshow.
            @type slide_id: string
            @param config - Contains the control configurations.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            endpoint = self.endpoint + "/slides/" + slide_id
            self.ac.send_api_request("PUT", endpoint, config, self.request_headers)

        def delete_slideshow(self, slide_id):
            """
            Delete a specified slideshow in the workspace.
            @param slide_id: Id of the slideshow.
            @type slide_id: string
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            endpoint = self.endpoint + "/slides/" + slide_id
            self.ac.send_api_request("DELETE", endpoint, None, self.request_headers)

        def get_slideshows(self):
            """
            Returns list of slideshows for the specified workspace.
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return: Slideshow list.
            @rtype:list
            """
            endpoint = self.endpoint + "/slides"
            response = self.ac.send_api_request("GET", endpoint, None, self.request_headers)
            return response["data"]["slideshows"]

        def get_slideshow_url(self, slide_id, config={}):
            """
            Returns slide URL to access the specified slideshow.
            @param slide_id: Id of the slideshow.
            @type slide_id: string
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return: Slideshow URL.
            @rtype:string
            """
            endpoint = self.endpoint + "/slides/" + slide_id + "/publish"
            response = self.ac.send_api_request("GET", endpoint, config, self.request_headers)
            return response["data"]["slideUrl"]

        def get_slideshow_details(self, slide_id):
            """
            Returns details of the specified slideshow.
            @param slide_id: Id of the slideshow.
            @type slide_id: string
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return: Slideshow details.
            @rtype:dictionary
            """
            endpoint = self.endpoint + "/slides/" + slide_id
            response = self.ac.send_api_request("GET", endpoint, None, self.request_headers)
            return response["data"]["slideInfo"]

        def create_variable(self, variable_name, variable_datatype, variable_type, config={}):
            """
            Create a variable in the workspace.
            @param variable_name: Name of the variable to be created.
            @type variable_name: string
            @param variable_datatype: Datatype of the variable to be created.
            @type variable_datatype: string
            @param variable_type: Type of the variable to be created.
            @type variable_type: string
            @param config: Contains the control parameters.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return: Id of the created variable.
            @rtype:string
            """
            endpoint = self.endpoint + "/variables"
            config["variableName"] = variable_name
            config["variableDataType"] = variable_datatype
            config["variableType"] = variable_type
            response = self.ac.send_api_request("POST", endpoint, config, self.request_headers)
            return int(response["data"]["variableId"])

        def update_variable(self, variable_id, variable_name, variable_datatype, variable_type, config={}):
            """
            Update details of the specified variable in the workspace.
            @param variable_id: Id of the variable.
            @type variable_id: string
            @param variable_name: New name for the variable.
            @type variable_name: string
            @param variable_datatype: New datatype for the variable.
            @type variable_datatype: string
            @param variable_type: New type for the variable.
            @type variable_type: string
            @param config: Contains the control parameters.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            endpoint = self.endpoint + "/variables/" + variable_id
            config["variableName"] = variable_name
            config["variableDataType"] = variable_datatype
            config["variableType"] = variable_type
            response = self.ac.send_api_request("PUT", endpoint, config, self.request_headers)

        def delete_variable(self, variable_id):
            """
            Delete the specified variable in the workspace.
            @param variable_id: Id of the variable.
            @type variable_id: string
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            endpoint = self.endpoint + "/variables/" + variable_id
            response = self.ac.send_api_request("DELETE", endpoint, None, self.request_headers)

        def get_variables(self):
            """
            Returns list of variables for the specified workspace.
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return: Variable list.
            @rtype:list
            """
            endpoint = self.endpoint + "/variables"
            response = self.ac.send_api_request("GET", endpoint, None, self.request_headers)
            return response["data"]["variables"]

        def get_variable_details(self, variable_id):
            """
            Returns list of variables for the specified workspace.
            @param variable_id: Id of the variable.
            @type variable_id: string
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return: Variable details.
            @rtype:dictionary
            """
            endpoint = self.endpoint + "/variables/" + variable_id
            response = self.ac.send_api_request("GET", endpoint, None, self.request_headers)
            return response["data"]

        def make_default_folder(self, folder_id):
            """
            Make the specified folder as default.
            @param folder_id: Id of the folder.
            @type folder_id: string
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            endpoint = self.endpoint + "/folders/" + folder_id + "/default"
            response = self.ac.send_api_request("PUT", endpoint, None, self.request_headers)

        def get_datasources(self):
            """
            Returns list of datasources for the specified workspace.
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return: Datasource list.
            @rtype:list
            """
            endpoint = self.endpoint + "/datasources"
            response = self.ac.send_api_request("GET", endpoint, None, self.request_headers)
            return response["data"]["dataSources"]

        def sync_data(self, datasource_id, config={}):
            """
            Initiate data sync for the specified datasource.
            @param datasource_id: Id of the datasource.
            @type datasource_id: string
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            endpoint = self.endpoint + "/datasources/" + datasource_id + "/sync"
            response = self.ac.send_api_request("POST", endpoint, config, self.request_headers)

        def update_datasource_connection(self, datasource_id, config={}):
            """
            Update connection details for the specified datasource.
            @param datasource_id: Id of the datasource.
            @type datasource_id: string
            @param config: Contains the control parameters.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            endpoint = self.endpoint + "/datasources/" + datasource_id
            response = self.ac.send_api_request("PUT", endpoint, config, self.request_headers)

    class ViewAPI:
        """
        ViewAPI contains view level operations.
        """

        def __init__(self, ac, org_id, workspace_id, view_id):
            self.ac = ac
            self.endpoint = "/restapi/v2/workspaces/" + workspace_id + "/views/" + view_id
            self.request_headers = {}
            self.request_headers["ZANALYTICS-ORGID"] = org_id

        def rename(self, view_name, config={}):
            """
            Rename a specified view in the workspace.
            @param view_name: New name of the view.
            @type view_name: string
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            config["viewName"] = view_name
            response = self.ac.send_api_request("PUT", self.endpoint, config, self.request_headers)

        def delete(self, config={}):
            """
            Delete a specified view in the workspace.
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            response = self.ac.send_api_request("DELETE", self.endpoint, config, self.request_headers)

        def save_as(self, new_view_name, config={}):
            """
            Copy a specified view within the workspace.
            @param new_view_name: The name of the new view.
            @type new_view_name: string
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return: Created view id.
            @rtype:string
            """
            config["viewName"] = new_view_name
            endpoint = self.endpoint + "/saveas"
            response = self.ac.send_api_request("POST", endpoint, config, self.request_headers)
            return int(response["data"]["viewId"])

        def copy_formulas(self, formula_names, dest_workspace_id, config={}, dest_org_id=None):
            """
            Copy the specified formulas from one table to another within the workspace or across workspaces.
            @param formula_names: The name of the formula columns to be copied.
            @type formula_names: list
            @param dest_workspace_id: The ID of the destination workspace.
            @type dest_workspace_id: string
            @param dest_org_id: Id of the organization where the destination workspace is present. Can be C{None}.
            @type dest_org_id: string
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            config["formulaColumnNames"] = formula_names
            config["destWorkspaceId"] = dest_workspace_id
            endpoint = self.endpoint + "/formulas/copy"
            headers = self.request_headers.copy()
            if bool(dest_org_id):
                headers["ZANALYTICS-DEST-ORGID"] = dest_org_id
            self.ac.send_api_request("POST", endpoint, config, headers)

        def add_favorite(self):
            """
            Adds a specified view as favorite.
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            endpoint = self.endpoint + "/favorite"
            response = self.ac.send_api_request("POST", endpoint, None, self.request_headers)

        def remove_favorite(self):
            """
            Remove a specified view from favorite.
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            endpoint = self.endpoint + "/favorite"
            response = self.ac.send_api_request("DELETE", endpoint, None, self.request_headers)

        def create_similar_views(self, ref_view_id, folder_id, config={}):
            """
            Create reports for the specified table based on the reference table.
            @param ref_view_id: The ID of the reference view.
            @type ref_view_id: string
            @param folder_id: The folder id where the views to be saved.
            @type folder_id: string
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            config["referenceViewId"] = ref_view_id
            config["folderId"] = folder_id
            endpoint = self.endpoint + "/similarviews"
            self.ac.send_api_request("POST", endpoint, config, self.request_headers)

        def auto_analyse(self, config={}):
            """
            Auto generate reports for the specified table.
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            endpoint = self.endpoint + "/autoanalyse"
            self.ac.send_api_request("POST", endpoint, config, self.request_headers)

        def get_my_permissions(self):
            """
            Returns permissions for the specified view.
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return: Permission details.
            @rtype:dictionary
            """
            endpoint = self.endpoint + "/share/mypermissions"
            response = self.ac.send_api_request("GET", endpoint, None, self.request_headers)
            return response["data"]["permissions"]

        def get_view_url(self, config={}):
            """
            Returns the URL to access the specified view.
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return: View URL.
            @rtype:string
            """
            endpoint = self.endpoint + "/publish"
            response = self.ac.send_api_request("GET", endpoint, config, self.request_headers)
            return response["data"]["viewUrl"]

        def get_embed_url(self, config={}):
            """
            Returns embed URL to access the specified view.
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return: Embed URL.
            @rtype:string
            """
            endpoint = self.endpoint + "/publish/embed"
            response = self.ac.send_api_request("GET", endpoint, config, self.request_headers)
            return response["data"]["embedUrl"]

        def get_private_url(self, config={}):
            """
            Returns private URL to access the specified view.
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return: Private URL.
            @rtype:string
            """
            endpoint = self.endpoint + "/publish/privatelink"
            response = self.ac.send_api_request("GET", endpoint, config, self.request_headers)
            return response["data"]["privateUrl"]

        def create_private_url(self, config={}):
            """
            Create a private URL for the specified view.
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return: Private URL.
            @rtype:string
            """
            endpoint = self.endpoint + "/publish/privatelink"
            response = self.ac.send_api_request("POST", endpoint, config, self.request_headers)
            return response["data"]["privateUrl"]

        def add_column(self, column_name, data_type, config={}):
            """
            Add a column in the specified table.
            @param column_name: The name of the column.
            @type column_name: string
            @param data_type: The data-type of the column.
            @type data_type: string
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return: Created column id.
            @rtype:string
            """
            config["columnName"] = column_name
            config["dataType"] = data_type
            endpoint = self.endpoint + "/columns"
            response = self.ac.send_api_request("POST", endpoint, config, self.request_headers)
            return int(response["data"]["columnId"])

        def hide_columns(self, column_ids):
            """
            Hide the specified columns in the table.
            @param column_ids: Ids of the columns to be hidden.
            @type column_ids: list
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            config = {}
            config["columnIds"] = column_ids
            endpoint = self.endpoint + "/columns/hide"
            self.ac.send_api_request("PUT", endpoint, config, self.request_headers)

        def show_columns(self, column_ids):
            """
            Show the specified hidden columns in the table.
            @param column_ids: Ids of the columns to be shown.
            @type column_ids: list
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            config = {}
            config["columnIds"] = column_ids
            endpoint = self.endpoint + "/columns/show"
            self.ac.send_api_request("PUT", endpoint, config, self.request_headers)

        def add_row(self, column_values, config={}):
            """
            Add a single row in the specified table.
            @param column_values: Contains the values for the row. The column names are the key.
            @type column_values: dictionary
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return: Column Names and Added Row Values.
            @rtype:dictionary
            """
            config["columns"] = column_values
            endpoint = self.endpoint + "/rows"
            response = self.ac.send_api_request("POST", endpoint, config, self.request_headers)
            return response["data"]

        def update_row(self, column_values, criteria, config={}):
            """
            Update rows in the specified table.
            @param column_values: Contains the values for the row. The column names are the key.
            @type column_values: dictionary
            @param criteria: The criteria to be applied for updating data. Only rows matching the criteria will be updated. Should be null for update all rows.
            @type criteria: string
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return: Updated Columns List and Updated Rows Count.
            @rtype:dictionary
            """
            config["columns"] = column_values
            if criteria != None:
                config["criteria"] = criteria
            endpoint = self.endpoint + "/rows"
            response = self.ac.send_api_request("PUT", endpoint, config, self.request_headers)
            return response["data"]

        def delete_row(self, criteria, config={}):
            """
            Delete rows in the specified table.
            @param criteria: The criteria to be applied for deleting data. Only rows matching the criteria will be deleted. Should be null for delete all rows.
            @type criteria: string
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return: Deleted rows details.
            @rtype:string
            """
            if criteria != None:
                config["criteria"] = criteria
            endpoint = self.endpoint + "/rows"
            response = self.ac.send_api_request("DELETE", endpoint, config, self.request_headers)
            return response["data"]["deletedRows"]

        def rename_column(self, column_id, column_name, config={}):
            """
            Rename a specified column in the table.
            @param column_id: Id of the column.
            @type column_id: string
            @param column_name: New name for the column.
            @type column_name: string
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            config["columnName"] = column_name
            endpoint = self.endpoint + "/columns/" + column_id
            self.ac.send_api_request("PUT", endpoint, config, self.request_headers)

        def delete_column(self, column_id, config={}):
            """
            Delete a specified column in the table.
            @param column_id: Id of the column.
            @type column_id: string
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            endpoint = self.endpoint + "/columns/" + column_id
            self.ac.send_api_request("DELETE", endpoint, config, self.request_headers)

        def add_lookup(self, column_id, ref_view_id, ref_column_id, config={}):
            """
            Add a lookup in the specified child table.
            @param column_id: Id of the column.
            @type column_id: string
            @param ref_view_id: The id of the table contains the parent column.
            @type ref_view_id: string
            @param ref_column_id: The id of the parent column.
            @type ref_column_id: string
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            config["referenceViewId"] = ref_view_id;
            config["referenceColumnId"] = ref_column_id
            endpoint = self.endpoint + "/columns/" + column_id + "/lookup"
            self.ac.send_api_request("POST", endpoint, config, self.request_headers)

        def remove_lookup(self, column_id, config={}):
            """
            Remove the lookup for the specified column in the table.
            @param column_id: Id of the column.
            @type column_id: string
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            endpoint = self.endpoint + "/columns/" + column_id + "/lookup"
            self.ac.send_api_request("DELETE", endpoint, config, self.request_headers)

        def auto_analyse_column(self, column_id, config={}):
            """
            Auto generate reports for the specified column.
            @param column_id: Id of the column.
            @type column_id: string
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            endpoint = self.endpoint + "/columns/" + column_id + "/autoanalyse"
            self.ac.send_api_request("POST", endpoint, config, self.request_headers)

        def refetch_data(self, config={}):
            """
            Sync data from available datasource for the specified view.
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            endpoint = self.endpoint + "/sync"
            response = self.ac.send_api_request("POST", endpoint, config, self.request_headers)

        def get_last_import_details(self):
            """
            Returns last import details of the specified view.
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return: Last import details.
            @rtype:dictionary
            """
            endpoint = self.endpoint + "/importdetails"
            response = self.ac.send_api_request("GET", endpoint, None, self.request_headers)
            return response["data"]

    class BulkAPI:
        """
        BulkAPI contains data operations.
        """

        def __init__(self, ac, org_id, workspace_id):
            self.ac = ac
            self.endpoint = "/restapi/v2/workspaces/" + workspace_id
            self.bulk_endpoint = "/restapi/v2/bulk/workspaces/" + workspace_id
            self.request_headers = {}
            self.request_headers["ZANALYTICS-ORGID"] = org_id

        def import_data_in_new_table(self, table_name, file_type, auto_identify, file_path, config={}):
            """
            Create a new table and import the data contained in the mentioned file into the created table.
            @param table_name: Name of the new table to be created.
            @type table_name: string
            @param file_type: Type of the file to be imported.
            @type file_type: string
            @param auto_identify: Used to specify whether to auto identify the CSV format. Allowable values - true/false.
            @type auto_identify: string
            @param file_path: Path of the file to be imported.
            @type file_path: string
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return Import result
            @rtype:dictionary
            """
            endpoint = self.endpoint + "/data"
            config["tableName"] = table_name
            config["fileType"] = file_type
            config["autoIdentify"] = auto_identify
            response = self.ac.send_import_api_request(endpoint, config, self.request_headers, file_path)
            return response["data"]

        def import_raw_data_in_new_table(self, table_name, file_type, auto_identify, data, config={}):
            """
            Create a new table and import the raw data provided into the created table.
            @param table_name: Name of the new table to be created.
            @type table_name: string
            @param file_type: Type of the file to be imported.
            @type file_type: string
            @param auto_identify: Used to specify whether to auto identify the CSV format. Allowable values - true/false.
            @type auto_identify: string
            @param data: Raw data to be imported.
            @type data: string
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return Import result
            @rtype:dictionary
            """
            endpoint = self.endpoint + "/data"
            config["tableName"] = table_name
            config["fileType"] = file_type
            config["autoIdentify"] = auto_identify
            response = self.ac.send_import_api_request(endpoint, config, self.request_headers, None, data)
            return response["data"]

        def import_data(self, view_id, import_type, file_type, auto_identify, file_path, config={}):
            """
            Import the data contained in the mentioned file into the table.
            @param view_id: Id of the view where the data to be imported.
            @type view_id: string
            @param import_type: The type of import. Can be one of - append, truncateadd, updateadd.
            @type import_type: string
            @param file_type: Type of the file to be imported.
            @type file_type: string
            @param auto_identify: Used to specify whether to auto identify the CSV format. Allowable values - true/false.
            @type auto_identify: string
            @param file_path: Path of the file to be imported.
            @type file_path: string
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return Import result
            @rtype:dictionary
            """
            endpoint = self.endpoint + "/views/" + view_id + "/data"
            config["fileType"] = file_type
            config["autoIdentify"] = auto_identify
            config["importType"] = import_type
            response = self.ac.send_import_api_request(endpoint, config, self.request_headers, file_path)
            return response["data"]

        def import_raw_data(self, view_id, import_type, file_type, auto_identify, data, config={}):
            """
            Import the raw data provided into the table.
            @param view_id: Id of the view where the data to be imported.
            @type view_id: string
            @param import_type: The type of import. Can be one of - append, truncateadd, updateadd.
            @type import_type: string
            @param file_type: Type of the file to be imported.
            @type file_type: string
            @param auto_identify: Used to specify whether to auto identify the CSV format. Allowable values - true/false.
            @type auto_identify: string
            @param data: Raw data to be imported.
            @type data: string
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return Import result
            @rtype:dictionary
            """
            endpoint = self.endpoint + "/views/" + view_id + "/data"
            config["fileType"] = file_type
            config["autoIdentify"] = auto_identify
            config["importType"] = import_type
            response = self.ac.send_import_api_request(endpoint, config, self.request_headers, None, data)
            return response["data"]

        def import_bulk_data_in_new_table(self, table_name, file_type, auto_identify, file_path, config={}):
            """
            Asynchronously create a new table and import the data contained in the mentioned file into the created table.
            @param table_name: Name of the new table to be created.
            @type table_name: string
            @param file_type: Type of the file to be imported.
            @type file_type: string
            @param auto_identify: Used to specify whether to auto identify the CSV format. Allowable values - true/false.
            @type auto_identify: string
            @param file_path: Path of the file to be imported.
            @type file_path: string
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return Import job id
            @rtype:string
            """
            endpoint = self.bulk_endpoint + "/data"
            config["tableName"] = table_name
            config["fileType"] = file_type
            config["autoIdentify"] = auto_identify
            response = self.ac.send_import_api_request(endpoint, config, self.request_headers, file_path)
            return response["data"]["jobId"]

        def import_bulk_data(self, view_id, import_type, file_type, auto_identify, file_path, config={}):
            """
            Asynchronously import the data contained in the mentioned file into the table.
            @param view_id: Id of the view where the data to be imported.
            @type view_id: string
            @param import_type: The type of import. Can be one of - append, truncateadd, updateadd.
            @type import_type: string
            @param file_type: Type of the file to be imported.
            @type file_type: string
            @param auto_identify: Used to specify whether to auto identify the CSV format. Allowable values - true/false.
            @type auto_identify: string
            @param file_path: Path of the file to be imported.
            @type file_path: string
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return Import job id
            @rtype:string
            """
            endpoint = self.bulk_endpoint + "/views/" + view_id + "/data"
            config["fileType"] = file_type
            config["autoIdentify"] = auto_identify
            config["importType"] = import_type
            response = self.ac.send_import_api_request(endpoint, config, self.request_headers, file_path)
            return response["data"]["jobId"]

        def get_import_job_details(self, job_id):
            """
            Returns the details of the import job.
            @param job_id: Id of the job.
            @type job_id: string
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return Import job details
            @rtype:dictionary
            """
            endpoint = self.bulk_endpoint + "/importjobs/" + job_id
            response = self.ac.send_api_request("GET", endpoint, None, self.request_headers)
            return response["data"]

        def export_data(self, view_id, response_format, file_path, config={}):
            """
            Export the mentioned table (or) view data.
            @param view_id: Id of the view to be exported.
            @type view_id: string
            @param response_format: The format in which the data is to be exported.
            @type response_format: string
            @param file_path: Path of the file where the data exported to be stored.
            @type file_path: string
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            endpoint = self.endpoint + "/views/" + view_id + "/data"
            config["responseFormat"] = response_format
            self.ac.send_export_api_request(endpoint, config, self.request_headers, file_path)

        def initiate_bulk_export(self, view_id, response_format, config={}):
            """
            Initiate asynchronous export for the mentioned table (or) view data.
            @param view_id: Id of the view to be exported.
            @type view_id: string
            @param response_format: The format in which the data is to be exported.
            @type response_format: string
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return Export job id
            @rtype:string
            """
            endpoint = self.bulk_endpoint + "/views/" + view_id + "/data"
            config["responseFormat"] = response_format
            response = self.ac.send_api_request("GET", endpoint, config, self.request_headers)
            return response["data"]["jobId"]

        def initiate_bulk_export_using_sql(self, sql_query, response_format, config={}):
            """
            Initiate asynchronous export with the given SQL Query.
            @param sql_query: The SQL Query whose output is exported.
            @type sql_query: string
            @param response_format: The format in which the data is to be exported.
            @type response_format: string
            @param config: Contains any additional control parameters. Can be C{None}.
            @type config:dictionary
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return Export job id
            @rtype:string
            """
            endpoint = self.bulk_endpoint + "/data"
            config["responseFormat"] = response_format
            config["sqlQuery"] = sql_query
            response = self.ac.send_api_request("GET", endpoint, config, self.request_headers)
            return response["data"]["jobId"]

        def get_export_job_details(self, job_id):
            """
            Returns the details of the export job.
            @param job_id: Id of the export job.
            @type job_id: string
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            @return Export job details
            @rtype:dictionary
            """
            endpoint = self.bulk_endpoint + "/exportjobs/" + job_id
            response = self.ac.send_api_request("GET", endpoint, None, self.request_headers)
            return response["data"]

        def export_bulk_data(self, job_id, file_path):
            """
            Download the exported data for the mentioned job id.
            @param job_id: Id of the job to be exported.
            @type job_id: string
            @param file_path: Path of the file where the data exported to be stored.
            @type file_path: string
            @raise ServerError: If the server has received the request but did not process the request due to some error.
            @raise ParseError: If the server has responded but client was not able to parse the response.
            """
            endpoint = self.bulk_endpoint + "/exportjobs/" + job_id + "/data"
            self.ac.send_export_api_request(endpoint, None, self.request_headers, file_path)

    def set_proxy(self, proxy_host, proxy_port, proxy_user_name, proxy_password):
        """
        Internal method to handle proxy details.
        """
        self.proxy = True
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.proxy_user_name = proxy_user_name
        self.proxy_password = proxy_password

    def send_import_api_request(self, request_url, config, request_headers, file_path, data=None):
        """
        Internal method to handle HTTP request.
        """
        if self.access_token == None:
            self.regenerate_analytics_oauth_token()

        request_url = self.analytics_server_url + request_url
        config_data = None
        if bool(config):
            config_data = "CONFIG=" + urllib.parse.quote_plus(json.dumps(config))

        if bool(data):
            if (bool(config_data)):
                config_data += "&"
            else:
                config_data = ""

            config_data += "DATA=" + urllib.parse.quote_plus(json.dumps(data))
            resp_obj = self.submit_import_request(request_url, config_data, request_headers, self.access_token)
        else:
            files = {'FILE': open(file_path, 'rb')}
            resp_obj = self.submit_import_request(request_url, config_data, request_headers, self.access_token, files)

        if not (str(resp_obj.status_code).startswith("2")):
            if (self.is_oauth_expired(resp_obj)):
                self.regenerate_analytics_oauth_token()
                if bool(data):
                    resp_obj = self.submit_import_request(request_url, config_data, request_headers, self.access_token)
                else:
                    resp_obj = self.submit_import_request(request_url, config_data, request_headers, self.access_token,
                                                          files)
                if not (str(resp_obj.status_code).startswith("2")):
                    raise ServerError(resp_obj.resp_content, False)
            else:
                raise ServerError(resp_obj.resp_content, False)

        response = resp_obj.resp_content
        response = json.loads(response)
        return response

    def submit_import_request(self, request_url, parameters, request_headers={}, access_token=None, files=None):
        """
        Internal method to send request to server.
        """
        try:
            if request_headers == None:
                request_headers = {}

            if access_token != None:
                request_headers["Authorization"] = "Zoho-oauthtoken " + access_token

            request_headers["User-Agent"] = "Analytics Python Client v" + self.CLIENT_VERSION

            req_obj = req_obj = requests.Session()
            if self.proxy:
                proxy_details = {
                    "http": "http://" + self.proxy_host + ":" + self.proxy_port,
                    "https": "http://" + self.proxy_host + ":" + self.proxy_port
                }
                req_obj.proxies = proxy_details
                if self.proxy_user_name != None and self.proxy_password != None:
                    proxy_auth_details = HTTPProxyDigestAuth(self.proxy_user_name, self.proxy_password)
                    req_obj.auth = proxy_auth_details

            if bool(files):
                resp_obj = req_obj.post(request_url, params=parameters, files=files, headers=request_headers)
            else:
                resp_obj = req_obj.post(request_url, params=parameters, headers=request_headers)

            resp_obj = response_obj(resp_obj)
        except Exception as ex:
            resp_obj = response_obj(ex)

        return resp_obj

    def send_export_api_request(self, request_url, config, request_headers, file_path):
        """
        Internal method to handle HTTP request.
        """
        file = open(file_path, "wb")

        if self.access_token == None:
            self.regenerate_analytics_oauth_token()

        request_url = self.analytics_server_url + request_url
        config_data = None
        if bool(config):
            config_data = "CONFIG=" + urllib.parse.quote_plus(json.dumps(config))

        resp_obj = self.submit_export_request(request_url, config_data, request_headers, self.access_token)

        if not (str(resp_obj.status_code).startswith("2")):
            resp_obj = response_obj(resp_obj)
            if (self.is_oauth_expired(resp_obj)):
                self.regenerate_analytics_oauth_token()
                resp_obj = self.submit_export_request(request_url, config_data, request_headers, self.access_token)
                if not (str(resp_obj.status_code).startswith("2")):
                    raise ServerError(resp_obj.resp_content, False)
            else:
                raise ServerError(resp_obj.resp_content, False)

        file.write(resp_obj.content)
        file.close()
        return

    def submit_export_request(self, request_url, parameters, request_headers={}, access_token=None):
        """
        Internal method to send request to server.
        """
        try:
            if request_headers == None:
                request_headers = {}

            if access_token != None:
                request_headers["Authorization"] = "Zoho-oauthtoken " + access_token

            request_headers["User-Agent"] = "Analytics Python Client v" + self.CLIENT_VERSION

            req_obj = req_obj = requests.Session()
            if self.proxy:
                proxy_details = {
                    "http": "http://" + self.proxy_host + ":" + self.proxy_port,
                    "https": "http://" + self.proxy_host + ":" + self.proxy_port
                }
                req_obj.proxies = proxy_details
                if self.proxy_user_name != None and self.proxy_password != None:
                    proxy_auth_details = HTTPProxyDigestAuth(self.proxy_user_name, self.proxy_password)
                    req_obj.auth = proxy_auth_details

            resp_obj = req_obj.get(request_url, params=parameters, headers=request_headers)

        except Exception as ex:
            resp_obj = response_obj(ex)

        return resp_obj

    def send_api_request(self, request_method, request_url, config, request_headers, is_json_response=True):
        """
        Internal method to handle HTTP request.
        """
        if self.access_token == None:
            self.regenerate_analytics_oauth_token()

        request_url = self.analytics_server_url + request_url
        config_data = None
        if bool(config):
            config_data = "CONFIG=" + urllib.parse.quote_plus(json.dumps(config))

        resp_obj = self.submit_request(request_method, request_url, config_data, request_headers, self.access_token)

        if not (str(resp_obj.status_code).startswith("2")):
            if (self.is_oauth_expired(resp_obj)):
                self.regenerate_analytics_oauth_token()
                resp_obj = self.submit_request(request_method, request_url, config_data, request_headers,
                                               self.access_token)
                if not (str(resp_obj.status_code).startswith("2")):
                    raise ServerError(resp_obj.resp_content, False)
            else:
                raise ServerError(resp_obj.resp_content, False)

        # API success - No response case
        if (str(resp_obj.status_code) != "200"):
            return

        response = resp_obj.resp_content
        if is_json_response:
            response = json.loads(response)
        return response

    def submit_request(self, request_method, request_url, parameters, request_headers={}, access_token=None):
        """
        Internal method to send request to server.
        """
        try:
            if request_headers == None:
                request_headers = {}

            if access_token != None:
                request_headers["Authorization"] = "Zoho-oauthtoken " + access_token

            request_headers["User-Agent"] = "Analytics Python Client v" + self.CLIENT_VERSION

            req_obj = req_obj = requests.Session()
            if self.proxy:
                proxy_details = {
                    "http": "http://" + self.proxy_host + ":" + self.proxy_port,
                    "https": "http://" + self.proxy_host + ":" + self.proxy_port
                }
                req_obj.proxies = proxy_details
                if self.proxy_user_name != None and self.proxy_password != None:
                    proxy_auth_details = HTTPProxyDigestAuth(self.proxy_user_name, self.proxy_password)
                    req_obj.auth = proxy_auth_details

            resp_obj = None

            if request_method == "GET":
                resp_obj = req_obj.get(request_url, params=parameters, headers=request_headers)
            elif request_method == "POST":
                resp_obj = req_obj.post(request_url, params=parameters, headers=request_headers)
            elif request_method == "PUT":
                resp_obj = req_obj.put(request_url, params=parameters, headers=request_headers)
            elif request_method == "DELETE":
                resp_obj = req_obj.delete(request_url, params=parameters, headers=request_headers)

            resp_obj = response_obj(resp_obj)
        except Exception as ex:
            resp_obj = response_obj(ex)

        return resp_obj

    def get_request_obj(self):
        """
        Internal method for getting OAuth token.
        """
        req_obj = requests.Session()

        if self.proxy:
            proxy_details = {
                "http": "http://" + self.proxy_host + ":" + self.proxy_port,
                "https": "http://" + self.proxy_host + ":" + self.proxy_port
            }
            req_obj.proxies = proxy_details
            if self.proxy_user_name != None and self.proxy_password != None:
                proxy_auth_details = HTTPProxyDigestAuth(self.proxy_user_name, self.proxy_password)
                req_obj.auth = proxy_auth_details
        return request_obj

    def is_oauth_expired(self, resp_obj):
        """
        Internal method to check whether the accesstoken expired or not.
        """
        try:
            resp_content = json.loads(resp_obj.resp_content)
            err_code = resp_content["data"]["errorCode"]
            return err_code == 8535
        except Exception:
            return False

    def regenerate_analytics_oauth_token(self):
        """
        Internal method for getting OAuth token.
        """
        oauth_params = {}
        oauth_params["client_id"] = self.client_id
        oauth_params["client_secret"] = self.client_secret
        oauth_params["refresh_token"] = self.refresh_token
        oauth_params["grant_type"] = "refresh_token"
        oauth_params = urllib.parse.urlencode(oauth_params)  # .encode(self.COMMON_ENCODE_CHAR)
        req_url = self.accounts_server_url + "/oauth/v2/token"
        oauth_resp_obj = self.submit_request("POST", req_url, oauth_params)

        if (oauth_resp_obj.status_code == 200):
            oauth_json_resp = json.loads(oauth_resp_obj.resp_content)
            if ("access_token" in oauth_json_resp):
                self.access_token = oauth_json_resp["access_token"]
                return

        raise ServerError(oauth_resp_obj.resp_content, True)


class response_obj:
    """
    Internal class.
    """

    def __init__(self, resp_obj):
        self.resp_content = resp_obj.text
        self.status_code = resp_obj.status_code
        self.headers = resp_obj.headers


class ServerError(Exception):
    """
    ServerError is thrown if the analytics server has received the request but did not process the
    request due to some error. For example if authorization failure.
    """

    def __init__(self, response, is_IAM_Error):
        self.errorCode = 0
        self.message = response

        try:
            error_data = json.loads(response)
            if is_IAM_Error:
                self.message = "Exception while generating oauth token. Response - " + response
            else:
                self.errorCode = error_data["data"]["errorCode"]
                self.message = error_data["data"]["errorMessage"]
        except Exception as inst:
            print(inst)
            self.parseError = inst

    def __str__(self):
        return repr(self.message)


class ParseError(Exception):
    """
    ParseError is thrown if the server has responded but client was not able to parse the response.
    Possible reasons could be version mismatch.The client might have to be updated to a newer version.
    """

    def __init__(self, responseContent, message, origExcep):
        self.responseContent = responseContent  #: The complete response content as sent by the server.
        self.message = message  #: The message describing the error.
        self.origExcep = origExcep  #: The original exception that occurred during parsing(Can be C{None}).

    def __str__(self):
        return repr(self.message)
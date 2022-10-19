import frappe

# for referance 
# https://github.com/Porter97/Python-Medium

from os.path import basename
try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

import requests

BASE_PATH = "https://api.medium.com"


class Client(object):
    """A client for the Medium OAuth2 REST API."""

    def __init__(self, application_id=None, application_secret=None,
                 access_token=None):
        self.application_id = application_id
        self.application_secret = application_secret
        self.access_token = access_token

    def get_authorization_url(self, state, redirect_url, scopes):
        """Get a URL for users to authorize the application.
        :param str state: A string that will be passed back to the redirect_url
        :param str redirect_url: The URL to redirect after authorization
        :param list scopes: The scopes to grant the application
        :returns: str
        """
        qs = {
            "client_id": self.application_id,
            "scope": ",".join(scopes),
            "state": state,
            "response_type": "code",
            "redirect_uri": redirect_url,
        }

        return "https://medium.com/m/oauth/authorize?" + urlencode(qs)
    
    def get_current_user(self):
        """Fetch the data for the currently authenticated user.
        Requires the 'basicProfile' scope.
        :returns: A dictionary with the users data ::
            {
                'username': 'kylehg',
                'url': 'https://medium.com/@kylehg',
                'imageUrl': 'https://cdn-images-1.medium.com/...',
                'id': '1f86...',
                'name': 'Kyle Hardgrave'
            }
        """
        return self._request("GET", "/v1/me")
    
    def upload_image(self, file_path, content_type):
        """Upload a local image to medium for use in a post.
        Requires the ``uploadImage`` scope.
        :param str file_path: the file path of the image
        :param str content_type: The type of the image. Valid values are
            ``image/jpeg``, ``image/png``, ``image/gif``, and ``image/tiff``.
        :return: A dictionary with the image data ::
            {
                'url': 'https://cdn-images-1.medium.com/0*dlkfjalksdjfl.jpg',
                'md5': 'd87e1628ca597d386e8b3e25de3a18b8'
            }
        """
        with open(file_path, "rb") as f:
            filename = basename(file_path)
            files = {"image": (filename, f, content_type)}
            return self._request("POST", "/v1/images", files=files)

    def create_post(self, user_id, title, content, content_format, tags=None,
                        canonical_url=None, publish_status=None, license=None,
                        publication_id=None, notify_followers=False):
            """Create a post for the current user
            Requires the 'publishPost' scope.
            :param str user_id: The application-specific user ID as returned by
                ``get_current_user()``
            :param str title: The title of the post
            :param str content: The content of the post, in HTML or Markdown
            :param str content_format: The format of the post content, either
                ``html`` or ``markdown``
            :param list tags: (optional), List of tags for the post, max 3
            :param str canonical_url: (optional), A rel="canonical" link for
                the post
            :param str publish_status: (optional), What to publish the post as,
                either ``public``, ``unlisted``, or ``draft``. Defaults to
                ``public``.
            :param license: (optional), The license to publish the post under:
                - ``all-rights-reserved`` (default)
                - ``cc-40-by``
                - ``cc-40-by-sa``
                - ``cc-40-by-nd``
                - ``cc-40-by-nc``
                - ``cc-40-by-nc-nd``
                - ``cc-40-by-nc-sa``
                - ``cc-40-zero``
                - ``public-domain``
            :param str publication_id: (optional), The id of the publication the post
                is being created under.
            :param bool notify_followers: (optional), Whether to notify followers that
                the user has published.
            :returns: A dictionary with the post data ::
                {
                    'canonicalUrl': '',
                    'license': 'all-rights-reserved',
                    'title': 'My Title',
                    'url': 'https://medium.com/@kylehg/55050649c95',
                    'tags': ['python', 'is', 'great'],
                    'authorId': '1f86...',
                    'publishStatus': 'draft',
                    'id': '55050649c95'
                    'publicationId': '123456789' (only if created under a publication)
                }
            """
            data = {
                "title": title,
                "content": content,
                "contentFormat": content_format,
            }

            if tags:
                data["tags"] = tags
            if canonical_url:
                data["canonicalUrl"] = canonical_url
            if publish_status:
                data["publishStatus"] = publish_status
            if license:
                data["license"] = license
            if notify_followers:
                data["notifyFollowers"] = notify_followers

            if publication_id:
                path = "/v1/publications/%s/posts" % publication_id
            else:
                path = "/v1/users/%s/posts" % user_id

            return self._request("POST", path, json=data)

    def _request(self, method, path, alt_path=False, json=None, form_data=None, files=None):
        """Make a signed request to the given route."""
        if alt_path:
            url = "https://api.rss2json.com/v1/api.json?rss_url=https://medium.com" + path
        else:
            url = BASE_PATH + path
        headers = {
            "Accept": "application/json",
            "Accept-Charset": "utf-8",
            "Authorization": "Bearer %s" % self.access_token,
        }

        resp = requests.request(method, url, json=json, data=form_data,
                                files=files, headers=headers)
        json = resp.json()
        if 200 <= resp.status_code < 300:
            try:
                return json["data"]
            except KeyError:
                return json

        raise MediumError("API request failed", json)


class MediumError(Exception):
    """Wrapper for exceptions generated by the Medium API."""

    def __init__(self, message, resp={}):
        self.resp = resp
        try:
            error = resp["errors"][0]
        except KeyError:
            error = {}
        self.code = error.get("code", -1)
        self.msg = error.get("message", message)
        super(MediumError, self).__init__(self.msg)



@frappe.whitelist()
def mediumpost(doc,method):
    medium_credential=frappe.get_single('Medium Credential')
   
    token = medium_credential.get_password('token')
    passw = medium_credential.get_password('user_password')
    name = medium_credential.user_id
   
    def get_absolute_path(file_name, is_private=False):
        if(file_name.startswith('/files/')):
            file_name = file_name[7:]
        return frappe.utils.get_bench_path()+ "/sites/" + frappe.utils.get_path('private' if is_private else 'public', 'files', file_name)[2:]

    
    try:
        client = Client(application_id=name, application_secret=passw,access_token=token)
        user = client.get_current_user()
        tags = None
        if doc.tags_with_comma_seperated:
            tags = doc.tags_with_comma_seperated.split(',')

        # for future referance (not used until now)
        # image_address = get_absolute_path(doc.image123)
        # image = client.upload_image(image_address, 'image/jpeg')
        if doc.image_url:
            image = doc.image_url
        else:
            image = None

        # print(image,type(image))
        client.create_post(user_id=user["id"], title=doc.name, content=f"<h1>{doc.story_heading}</h1><img src={image}><p>{doc.content}</p>",tags=tags,
                                content_format="html", publish_status=doc.public_status, publication_id=None,
                                notify_followers=True)

        frappe.msgprint(msg = 'Post has been created',
                                title = 'Message',
                                indicator = 'green')

    except:
        frappe.msgprint(msg = 'Something Went Wrong',
                                    title = 'Message',
                                    indicator = 'red')




# for further use
# feed = client.list_articles(user['username'])

# print(feed[1])

	


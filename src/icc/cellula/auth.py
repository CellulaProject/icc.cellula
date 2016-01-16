from zope.interface import Interface
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from icc.rdfservice.interfaces import IRDFStorage, IGraph
import logging
logger=logging.getLogger('icc.cellula')

def auth_callback(userid, request):
    logger.warning("No User Storage implemented Yet.")
    return None

_marker=object()

class AuthenticationPolicy(AuthTktAuthenticationPolicy):
    def __init__(self,
                secret='cll_sec',
                cookie_name='cll_tkt',
                secure=False,
                include_ip=False,
                timeout=None,
                reissue_time=None,
                max_age=None,
                path="/",
                http_only=False,
                wild_domain=True,
                debug=False,
                hashalg=_marker,
                parent_domain=False,
                domain=None):

        if hashalg==_marker:
            hashalg="sha512"

        callback=auth_callback

        AuthTktAuthenticationPolicy.__init__(self,
                      secret=secret,
                      cookie_name=cookie_name,
                      secure=secure,
                      include_ip=include_ip,
                      timeout=timeout,
                      reissue_time=reissue_time,
                      max_age=max_age,
                      path=path,
                      http_only=http_only,
                      wild_domain=wild_domain,
                      debug=debug,
                      hashalg=hashalg,
                      parent_domain=parent_domain,
                      domain=domain)

class AuthorizationPolicy(ACLAuthorizationPolicy):
    pass

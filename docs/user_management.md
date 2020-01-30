# User Management
## Overview
Currently user management on OPC-UA servers here is done exclusively through certificates, though there is the potential to create new user management objects.

How this works in practice is that every user generates a certificate/private key pair, and then the certificate is given
to the OPC-UA server. The administrator of the OPC-UA server enters the certificate into the `certificate_user_manager` with a `UserRole`
and a `name`. When a user connects with this certificate, every action they do will be associated with their name in the logs,
and the `permission_ruleset` will determine whether a user with that role can carry out that action.

## Usage
an example of usage is in `examples/server-with-encryption.py`:
```python
user_manager = CertificateUserManager()
await user_manager.add_user("certificates/peer-certificate-example-1.der", name='user1')

server = Server(user_manager=user_manager)
await server.init()
server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
server.set_security_policy([ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt],
                           permission_ruleset=SimpleRoleRuleset())
```

We can see here that a certificate user manager object is made, and told to assign peer-certificate-example-1 with User credentials.

When the client wants to actually carry out some actions, the user manager `CertificateUserManager` will use the 
certificate handler to associate a user to the certificate, and then the `permission_ruleset` will determine if they are
allowed to do the action.


## Custom permission rules
The permission ruleset object has been designed in a way to allow new rulesets to be made easily. For example, lets look
at the implementation of `SimpleRoleRuleset`:
```python
class SimpleRoleRuleset(PermissionRuleset):
    """
    Standard simple role-based ruleset.
    Admins alone can write, admins and users can read, and anonymous users can't do anything.
    """

    def __init__(self):
        write_ids = list(map(ua.NodeId, WRITE_TYPES))
        read_ids = list(map(ua.NodeId, READ_TYPES))
        self._permission_dict = {
            UserRole.Admin: set().union(write_ids, read_ids),
            UserRole.User: set().union(read_ids),
            UserRole.Anonymous: set()
        }

    def check_validity(self, user, action_type_id, body):
        if action_type_id in self._permission_dict[user.role]:
            return True
        else:
            return False
```

all that is needed to create a permission ruleset is to create a function `check_validity` which takes information about
the user and the action type, and returns `True` if it is allowed, or `False` if it isn't. In this case, we simply take the
user role and compare the action it wants to do with a list of actions stored in a dictionary. A more complex ruleset could use the body
of the request to determine some users as being able to write some variables, but not others. Another potential option is 
having more user roles than those we have set here. 
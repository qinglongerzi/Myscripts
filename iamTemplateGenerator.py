#!/usr/bin/env python3

import json
import re

class Template(object):
    """docstring for Template"""
    def __init__(self):
        super(Template, self).__init__()
        # list of tuple for keeping resources and outputs order
        self.resources = []
        self.outputs = []
        self.template = {
                            'AWSTemplateFormatVersion': '2010-09-09'
                        }

    def add_resources(self, resources):
        """Add resources to template

        Args:
            resources (list of Resource)
        """
        for resource in resources:
            self.resources.extend(resource.get_template())
            if resource.get_output() is not None:
                self.outputs.append(resource.get_output())

    def to_json(self):
        """Transform template to json
        """
        self.template['Resources'] = dict(self.resources)
        self.template['Outputs'] = dict(self.outputs)
        return json.dumps(self.template)


class Resource(object):
    """docstring for Resource"""
    def __init__(self, resource_name, resource_type):
        super(Resource, self).__init__()
        non_alphanumeric_regex = re.compile('[^a-zA-Z0-9]')
        self.resource_name = non_alphanumeric_regex.sub('', resource_name)
        self.resource_type = resource_type
        self.template = (
            self.resource_name,
            {
                'Type': self.resource_type,
                'Properties': {}
            }
        )
        self.extra_template = []
        self.output = None

    def _properties(self):
        """Get properties
           This function would be used by Class Resource ONLY
        """
        return self.template[1]['Properties']

    def _self(self, value):
        try:
            return value.get_self()
        except:
            return value

    def string_join(self, delimiter, value_list):
        """Use CloudFormation syntax to join values

        Args:
            delimiter (str)
            value_list (list)
        """
        return {'Fn::Join': [delimiter, value_list]}

    def set_property(self, property_name, property_value):
        """Set property value

        Args:
            property_name (str)
            property_value (anytype)
        """
        self._properties()[property_name] = self._self(property_value)

    def add_property(self, property_name, property_value):
        """Add property value to the property_name

        Args:
            property_name (str)
            property_value (anytype)
        """
        if property_name in self._properties():
            self._properties()[property_name].append(self._self(property_value))
        else:
            self._properties()[property_name] = [self._self(property_value)]

    def set_output(self, key, value, description):
        """Set output part of the template

        Args:
            key (str)
            value (anytype)
            description (str)
        """
        self.output = (
            key,
            {
                'Description': description,
                'Value': value
            }
        )

    def get_output(self):
        """Get output part of the template
        """
        return self.output

    def get_self(self):
        """Get resource itself by CloudFormation syntax
        """
        return {"Ref": self.resource_name}

    def get_template(self):
        """Get template of the resource, not include output part
        """
        template = self.extra_template.copy()
        template.append(self.template)
        return template

    def set_default_output(self):
        """Set default output part
        """
        self.set_output(self.resource_name, self.string_join(' : ', ['Name', self.get_self()]) , '%s is created' %  self.resource_name)

    def get_resource_name(self):
        return self.resource_name

    def add_template(self, template):
        self.extra_template.extend(template)


class UserGroup(Resource):
    """docstring for UserGroup"""
    def __init__(self, resource_name):
        super(UserGroup, self).__init__(resource_name, 'AWS::IAM::Group')

    def set_name(self, group_name):
        self.set_property('GroupName', group_name)

    def attach_managed_policy(self, managed_policy_arns=None, managed_policies=None):
        if managed_policy_arns is not None:
            self.set_property('ManagedPolicyArns', managed_policy_arns)

        if managed_policies is not None:
            for policy in managed_policies:
                policy.add_user_group(self.get_self())


class ManagedPolicy(Resource):
    """docstring for ManagedPolicy"""
    def __init__(self, resource_name):
        super(ManagedPolicy, self).__init__(resource_name, 'AWS::IAM::ManagedPolicy')

    def set_name(self, policy_name):
        self.set_property('ManagedPolicyName', policy_name)

    def set_description(self, description):
        self.set_property('Description', description)

    def add_user_group(self, user_group):
        self.add_property('Groups', user_group)

    def add_user(self, user):
        self.add_property('Users', user)

    def set_policy_statement(self, statement):
        self.set_property('PolicyDocument', {
                                                "Version": "2012-10-17",
                                                "Statement": statement
                                            }
                         )


class AccessKey(Resource):
    """docstring for AccessKey"""
    def __init__(self, resource_name):
        super(AccessKey, self).__init__(resource_name, 'AWS::IAM::AccessKey')

    def set_user(self, user):
        self.set_property('UserName', user)

    def get_access_key(self):
        return self.get_self()

    def get_secret_key(self):
        return {'Fn::GetAtt': [self.resource_name, 'SecretAccessKey']}

    def set_default_output(self):
        self.set_output(self.resource_name, self.string_join(',', [self.get_access_key(), self.get_secret_key()]), '%s is created' % self.resource_name)


class User(Resource):
    """docstring for User"""
    def __init__(self, resource_name):
        super(User, self).__init__(resource_name, 'AWS::IAM::User')

    def set_name(self, user_name):
        self.set_property('UserName', user_name)

    def set_access_key(self):
        access_key = AccessKey('%sAccessKey' % self.resource_name)
        access_key.set_user(self.get_self())
        access_key.set_default_output()
        return access_key

    def attach_managed_policy(self, managed_policy_arns):
        self.set_property('ManagedPolicyArns', managed_policy_arns)

    def add_inline_policy(self, policy_name, policy_statement):
        self.add_property('Policies',   {
                                            'PolicyName': policy_name,
                                            'PolicyDocument': {
                                                'Version': '2012-10-17',
                                                'Statement': policy_statement
                                            }
                                        }
                         )

    def add_custom_managed_policy(self, policy_name, policy_description, policy_statement):
        managed_policy = ManagedPolicy('%sPolicy' % self.resource_name)
        managed_policy.set_name(policy_name)
        managed_policy.set_description(policy_description)
        managed_policy.set_policy_statement(policy_statement)
        managed_policy.add_user(self.get_self())
        self.add_template(managed_policy.get_template())


class Role(Resource):
    """docstring for Role"""
    def __init__(self, resource_name):
        super(Role, self).__init__(resource_name, 'AWS::IAM::Role')

    def set_name(self, role_name):
        self.set_property('RoleName', role_name)

    def set_description(self, description):
        self.set_property('Description', description)

    def create_for_aws_service(self, service_name):
        policy_document =   {
                                'Statement': [{
                                    'Effect': 'Allow',
                                    'Principal': {
                                        'Service': ['%s.amazonaws.com' % service_name]
                                    },
                                    'Action': ['sts:AssumeRole']
                                }]
                            }
        self.set_property('AssumeRolePolicyDocument', policy_document)
        if service_name == 'ec2':
            profile_ec2 = InstanceProfile('%sProfile' % self.resource_name)
            profile_ec2.attach_roles([self.get_self()])
            self.add_template(profile_ec2.get_template())

    def attach_managed_policy(self, managed_policy_arns):
        self.set_property('ManagedPolicyArns', managed_policy_arns)

    def add_inline_policy(self, policy_name, policy_statement):
        self.add_property('Policies',   {
                                            'PolicyName': policy_name,
                                            'PolicyDocument': {
                                                'Version': '2012-10-17',
                                                'Statement': policy_statement
                                            }
                                        }
                         )


class InstanceProfile(Resource):
    """docstring for InstanceProfile"""
    def __init__(self, resource_name):
        super(InstanceProfile, self).__init__(resource_name, 'AWS::IAM::InstanceProfile')

    def attach_roles(self, roles):
        for role in roles:
            self.add_property('Roles', role)


def main():
    template = Template()

    user_group_admin = UserGroup('AdminGroup')
    user_group_user = UserGroup('UserGroup')

    policy_source_ip_restrition = ManagedPolicy('SourceIPRestriction')
    policy_iam_pass = ManagedPolicy('IAMPassRole')

    role_ec2 = Role('EC2Role')
    role_codedeploy = Role('CodeDeployServiceRole')

    user_codedeploy = User('CodeDeployUser')
    user_td_agent = User('TDAgentUser')

    policy_source_ip_restrition.set_name('SourceIPRestriction')
    policy_source_ip_restrition.set_description('Restricting Access by IP Address.Only allow from the office of Tecotec')
    policy_source_ip_restrition.set_policy_statement({
            "Sid": "SourceIPRestriction",
            "Effect": "Deny",
            "Action": "*",
            "Resource": "*",
            "Condition": {
                "NotIpAddress": {
                    "aws:SourceIp": [
                        "x.x.x.x/32"
                    ]
                }
            }
        })

    policy_iam_pass.set_name('IAMPassRole')
    policy_iam_pass.set_description('Allow PassRole for admin of Tecotec')
    policy_iam_pass.set_policy_statement({
            "Effect": "Allow",
            "Action": [
                "iam:Get*",
                "iam:List*",
                "iam:PassRole"
            ],
            "Resource": "*"
        })

    user_group_admin.set_name('tecotec-admin')
    user_group_admin.attach_managed_policy(managed_policy_arns=['arn:aws:iam::aws:policy/PowerUserAccess'],
                                           managed_policies=[policy_source_ip_restrition, policy_iam_pass])
    user_group_admin.set_default_output()

    user_group_user.set_name('tecotec-user')
    user_group_user.attach_managed_policy(managed_policy_arns=['arn:aws:iam::aws:policy/ReadOnlyAccess'],
                                          managed_policies=[policy_source_ip_restrition])
    user_group_user.set_default_output()
    
    role_ec2.set_name('EC2Role')
    role_ec2.set_description('A role for EC2. Allow get sorce code from s3. Allow get infomation of EC2 and put metrics to CloudWatch.')
    role_ec2.create_for_aws_service('ec2')
    role_ec2.attach_managed_policy([
            "arn:aws:iam::aws:policy/CloudWatchFullAccess",
            "arn:aws:iam::aws:policy/AmazonEC2ReadOnlyAccess",
            "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess",
            "arn:aws:iam::aws:policy/service-role/AWSCodeDeployRole"
        ])
    role_ec2.set_default_output()

    role_codedeploy.set_name('CodeDeployServiceRole')
    role_codedeploy.set_description('A role for CodeDeploy Service to run deployment')
    role_codedeploy.create_for_aws_service('codedeploy')
    role_codedeploy.attach_managed_policy(['arn:aws:iam::aws:policy/service-role/AWSCodeDeployRole'])
    role_codedeploy.set_default_output()

    user_codedeploy.set_name('CodeDeployUser')
    user_codedeploy_access_key = user_codedeploy.set_access_key()
    user_codedeploy.add_custom_managed_policy('CodeDeployUserPolicy',
                                            'The policy for the tool to use codedeploy.',
                                            {
                                                "Effect": "Allow",
                                                "Action": [
                                                    "s3:GetObject",
                                                    "s3:GetObjectVersion",
                                                    "s3:PutObject",
                                                    "s3:DeleteObject",
                                                    "codedeploy:ListApplications",
                                                    "codedeploy:ListDeploymentGroups",
                                                    "codedeploy:RegisterApplicationRevision",
                                                    "codedeploy:CreateDeployment",
                                                    "codedeploy:GetDeploymentConfig",
                                                    "codedeploy:GetApplicationRevision",
                                                    "codedeploy:GetDeployment"
                                                ],
                                                "Resource": "*"
                                            })
    user_codedeploy.set_default_output()

    
    user_td_agent.set_name('TDAgentUser')
    user_td_agent_access_key = user_td_agent.set_access_key()
    user_td_agent.add_custom_managed_policy('TDAgentUserPolicy',
                                            'The policy for td-agent.',
                                            {
                                                "Effect": "Allow",
                                                "Action": [
                                                    "logs:*",
                                                    "s3:GetObject",
                                                    "s3:PutObject"
                                                ],
                                                "Resource": "*"
                                            })
    user_td_agent.set_default_output()


    template.add_resources([user_group_admin,
                            user_group_user,
                            policy_source_ip_restrition,
                            policy_iam_pass,
                            role_ec2,
                            role_codedeploy,
                            user_codedeploy,
                            user_jenkins_access_key,
                            user_td_agent,
                            user_td_agent_access_key])


    with open('iam.tp', mode='w') as f:
        f.write(template.to_json())

if __name__ == '__main__':
    main()

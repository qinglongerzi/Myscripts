#!/usr/bin/env python3

import os
import json
import ipaddress
from optparse import OptionParser

def argsHandle():
    parser = OptionParser(description='', usage="python %prog -v vpc_cidrblock -n vpc_name [-m mask] [-e environment] [-r region] [-f function_zones] [-a availability_zones] [-o output]")
    parser.add_option('-v', dest='vpc_cidrblock', help='VPC CidrBlock. Example: \'10.167.0.0/16\'')
    parser.add_option('-m', dest='subnet_mask', default=21, type='int', help='Subnet mask. Example: \'-m 21\' means /21. Default 21')
    parser.add_option('-n', dest='vpc_name', help='VPC name without space.')
    parser.add_option('-e', dest='environment', default='dev,stg,pro', help='Evironments like dev, stg, pro. Divided by comma. Default \'dev,stg,pro\'')
    parser.add_option('-r', dest='region', default='ap-northeast-1', help='Region of VPC. Default \'ap-northeast-1\'')
    parser.add_option('-f', dest='function_zones', default='pub,web,pri', help='Function zones of subnets designed by creator. Divided by comma. Default \'pub,web,pri\'.')
    parser.add_option('-a', dest='availability_zones', default='ap-northeast-1d,ap-northeast-1c,ap-northeast-1a', help='Availability Zones of Region. Divided by comma. Default \'ap-northeast-1d,ap-northeast-1c,ap-northeast-1a\'.')
    parser.add_option('-o', dest='output', default='./vpc.tp', help='The file of template output. Default \'./vpc.tp\'')
    (opts, args) = parser.parse_args()
    if not opts.vpc_cidrblock:
        parser.error('-v option is required')
    if not opts.vpc_name:
        parser.error('-n option is required')
    try:
        vpc = ipaddress.IPv4Network(opts.vpc_cidrblock)
    except Exception as e:
        parser.error(e)

    if '/' not in opts.vpc_cidrblock:
        parser.error('Please input valid network. Example: \'10.167.0.0/16\'')

    if not vpc.is_private:
        parser.error('VPC CidrBlock is not a Private network.')

    vpc_mask = int(opts.vpc_cidrblock.split('/')[1])
    if vpc_mask > opts.subnet_mask:
        parser.error('Subnet mask invalid. Subnet mask: %d   VPC network mask: %d' % (opts.subnet_mask, vpc_mask))

    subnet_needed = len(opts.environment.split(',')) * len(opts.function_zones.split(',')) * len(opts.availability_zones.split(','))
    if len(list(vpc.subnets(prefixlen_diff=(opts.subnet_mask-vpc_mask)))) < subnet_needed:
        parser.error('The subnets are not enough. At least %s subnets are needed.' % subnet_needed)
    
    return opts

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
        self.resource_name = resource_name
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


class VPC(Resource):
    """docstring for VPC"""
    def __init__(self, resource_name):
        super(VPC, self).__init__(resource_name, 'AWS::EC2::VPC')

    def set_name(self, vpc_name):
        self.add_property('Tags', {
                                        'Key': 'Name',
                                        'Value': vpc_name
                                  })

    def set_network(self, cidrblock):
        self.set_property('CidrBlock', cidrblock)


class VPCGatewayAttachment(Resource):
    """docstring for VPCGatewayAttachment"""
    def __init__(self, resource_name):
        super(VPCGatewayAttachment, self).__init__(resource_name, 'AWS::EC2::VPCGatewayAttachment')

    def set_attachment(self, vpc, gateway):
        self.set_property('VpcId', vpc)
        self.set_property('InternetGatewayId', gateway)


class InternetGateway(Resource):
    """docstring for InternetGateway"""
    def __init__(self, resource_name):
        super(InternetGateway, self).__init__(resource_name, 'AWS::EC2::InternetGateway')

    def set_name(self, gateway_name):
        self.add_property('Tags', {
                                        'Key': 'Name',
                                        'Value': gateway_name
                                  })

    def vpc_attach(self, vpc):
        vpc_attachment = VPCGatewayAttachment('%sAttachment' % self.resource_name)
        vpc_attachment.set_attachment(vpc, self.get_self())
        self.add_template(vpc_attachment.get_template())
        

class Subnet(Resource):
    """docstring for Sub"""
    def __init__(self, resource_name):
        super(Subnet, self).__init__(resource_name, 'AWS::EC2::Subnet')

    def set_name(self, subnet_name):
        self.add_property('Tags', {
                                        'Key': 'Name',
                                        'Value': subnet_name
                                  })

    def set_availability_zone(self, availability_zone):
        self.set_property('AvailabilityZone', availability_zone)

    def set_cidrblock(self, cidrblock):
        self.set_property('CidrBlock', cidrblock)

    def set_vpc(self, vpc):
        self.set_property('VpcId', vpc)


class Route(Resource):
    """docstring for Route"""
    def __init__(self, resource_name):
        super(Route, self).__init__(resource_name, 'AWS::EC2::Route')

    def set_internet_gateway(self, internet_gateway):
        self.set_property('DestinationCidrBlock', '0.0.0.0/0')
        self.set_property('GatewayId', internet_gateway)

    def set_route_table(self, route_table):
        self.set_property('RouteTableId', route_table)


class SubnetRouteTableAssociation(Resource):
    """docstring for SubnetRouteTableAssociation"""
    def __init__(self, resource_name):
        super(SubnetRouteTableAssociation, self).__init__(resource_name, 'AWS::EC2::SubnetRouteTableAssociation')
    
    def set_subnet_associate(self, subnet, route_table):
        self.set_property('SubnetId', subnet)
        self.set_property('RouteTableId', route_table)
        

class RouteTable(Resource):
    """docstring for RouteTable"""
    def __init__(self, resource_name):
        super(RouteTable, self).__init__(resource_name, 'AWS::EC2::RouteTable')     

    def set_name(self, route_table_name):
        self.add_property('Tags', {
                                        'Key': 'Name',
                                        'Value': route_table_name
                                  })

    def set_vpc(self, vpc):
        self.set_property('VpcId', vpc)

    def subnet_associate(self, subnet):
        association = SubnetRouteTableAssociation('%sRouteTableAssociation' % subnet.get_resource_name())
        association.set_subnet_associate(subnet, self.get_self())
        self.add_template(association.get_template())

    def set_internet_gateway(self, internet_gateway):
        route = Route('%sRoute' % self.resource_name)
        route.set_internet_gateway(internet_gateway)
        route.set_route_table(self.get_self())
        self.add_template(route.get_template())


class SecurityGroupIngress(Resource):
    """docstring for SecurityGroupIngress"""
    def __init__(self, resource_name):
        super(SecurityGroupIngress, self).__init__(resource_name, 'AWS::EC2::SecurityGroupIngress')

    def set_description(self, description):
        self.set_property('Description', description)

    def set_group_id(self, security_group):
        self.set_property('GroupId', security_group)

    def set_protocal(self, protocal):
        self.set_property('IpProtocol', protocal)

    def set_source_group_id(self, security_group):
        self.set_property('SourceSecurityGroupId', security_group)


class SecurityGroup(Resource):
    """docstring for SecurityGroup"""
    def __init__(self, resource_name):
        super(SecurityGroup, self).__init__(resource_name, 'AWS::EC2::SecurityGroup')
    
    def set_name(self, security_group_name):
        self.set_property('GroupName', security_group_name)
        self.add_property('Tags', {
                                        'Key': 'Name',
                                        'Value': security_group_name
                                  })

    def set_description(self, description):
        self.set_property('GroupDescription', description)

    def add_ingress_rule(self, cidr_ip, protocal='-1', from_port=None, to_port=None, description=None):
        rule = {'CidrIp': cidr_ip, 'IpProtocol': protocal}
        if from_port is not None:
            rule['FromPort'] = from_port
            if to_port is None:
                rule['ToPort'] = from_port
            else:
                rule['ToPort'] = to_port
        elif to_port is not None:
            rule['FromPort'] = to_port
            rule['ToPort'] = to_port

        if description is not None:
            rule['Description'] = description

        self.add_property('SecurityGroupIngress', rule)

    def set_vpc(self, vpc):
        self.set_property('VpcId', vpc)

    def set_as_default_security_group(self):
        rule_ingress = SecurityGroupIngress('%sIngressRule' % self.get_resource_name())
        rule_ingress.set_group_id(self.get_self())
        rule_ingress.set_protocal('-1')
        rule_ingress.set_source_group_id(self.get_self())
        self.add_template(rule_ingress.get_template())


class VPCEndpoint(Resource):
    """docstring for VPCEndpoint"""
    def __init__(self, resource_name):
        super(VPCEndpoint, self).__init__(resource_name, 'AWS::EC2::VPCEndpoint')
        
    def set_route_tables(self, route_tables):
        for route_table in route_tables:
            self.add_property('RouteTableIds', route_table)

    def set_service_name(self, service_name):
        self.set_property('ServiceName', service_name)

    def set_endpoint_type(self, endpoint_type):
        self.set_property('VpcEndpointType', endpoint_type)

    def set_vpc(self, vpc):
        self.set_property('VpcId', vpc)


class DBSubnetGroup(Resource):
    """docstring for DBSubnetGroup"""
    def __init__(self, resource_name):
        super(DBSubnetGroup, self).__init__(resource_name, 'AWS::RDS::DBSubnetGroup')
        
    def set_name(self, subnet_group_name):
        self.set_property('DBSubnetGroupName', subnet_group_name)

    def set_description(self, description):
        self.set_property('DBSubnetGroupDescription', description)

    def add_subnet(self, subnet):
        self.add_property('SubnetIds', subnet)


class DBParameterGroup(Resource):
    """docstring for DBParameterGroup"""
    def __init__(self, resource_name):
        super(DBParameterGroup, self).__init__(resource_name, 'AWS::RDS::DBParameterGroup')
    
    def set_name(self, parameter_group_name):
        self.add_property('Tags', {
                                        'Key': 'Name',
                                        'Value': parameter_group_name
                                  })

    def set_description(self, description):
        self.set_property('Description', description)

    def set_family(self, family):
        self.set_property('Family', family)

    def update_parameters(self, parameter_pairs):
        """Update parameters in parameter group
           An array of parameter names and values for the parameter update. 
           At least one parameter name and value must be supplied. 
           You can modify a maximum of 20 parameters in a single request.
        """
        self.set_property('Parameters', parameter_pairs)
        

class DBClusterParameterGroup(Resource):
    """docstring for DBClusterParameterGroup"""
    def __init__(self, resource_name):
        super(DBClusterParameterGroup, self).__init__(resource_name, 'AWS::RDS::DBClusterParameterGroup')

    def set_name(self, parameter_group_name):
        self.add_property('Tags', {
                                        'Key': 'Name',
                                        'Value': parameter_group_name
                                  })

    def set_description(self, description):
        self.set_property('Description', description)

    def set_family(self, family):
        self.set_property('Family', family)

    def update_parameters(self, parameter_pairs):
        """Update parameters in parameter group
           An array of parameter names and values for the parameter update. 
           At least one parameter name and value must be supplied. 
           You can modify a maximum of 20 parameters in a single request.
        """
        self.set_property('Parameters', parameter_pairs)


class CacheSubnetGroup(Resource):
    """docstring for CacheSubnetGroup"""
    def __init__(self, resource_name):
        super(CacheSubnetGroup, self).__init__(resource_name, 'AWS::ElastiCache::SubnetGroup')
        
    def set_name(self, subnet_group_name):
        self.set_property('CacheSubnetGroupName', subnet_group_name)

    def set_description(self, description):
        self.set_property('Description', description)

    def add_subnet(self, subnet):
        self.add_property('SubnetIds', subnet)


class CacheParameterGroup(Resource):
    """docstring for CacheParameterGroup"""
    def __init__(self, resource_name):
        super(CacheParameterGroup, self).__init__(resource_name, 'AWS::ElastiCache::ParameterGroup')
    
    def set_description(self, description):
        self.set_property('Description', description)

    def set_family(self, family):
        self.set_property('CacheParameterGroupFamily', family)


def main():
    opts = argsHandle()
    vpc_cidrblock = opts.vpc_cidrblock
    subnet_cidrblocks = [str(s) for s in list(ipaddress.IPv4Network(vpc_cidrblock).subnets(prefixlen_diff=(opts.subnet_mask-int(opts.vpc_cidrblock.split('/')[1]))))]
    vpc_name = opts.vpc_name
    environment = opts.environment.split(',')
    function_zones = opts.function_zones.split(',')
    availability_zones = opts.availability_zones.split(',')
    region = opts.region

    template = Template()

    vpc = VPC('VPC')
    gateway = InternetGateway('InternetGateway')
    subnets = []
    route_tables = []
    security_groups = []
    db_subnet_groups = []
    cache_subnet_groups = []
    cnt = 0
    for env in environment:
        security_group_resouce_name = '%s%sDefaultSecurityGroup' % (vpc_name.capitalize(), env.capitalize())
        security_group_name = '%s-%s-default' % (vpc_name, env)
        security_group = SecurityGroup(security_group_resouce_name)
        security_group.set_name(security_group_name)
        security_group.set_description('Default security group for %s-%s' % (vpc_name, env))
        security_group.set_vpc(vpc)
        security_group.set_as_default_security_group()
        security_group.set_default_output()
        security_groups.append(security_group)

        db_subnet_group_resouce_name = '%s%sDBSubnetGroup' % (vpc_name.capitalize(), env.capitalize())
        db_subnet_group_name = '%s-%s-db-subnet-group' % (vpc_name, env)
        db_subnet_group = DBSubnetGroup(db_subnet_group_resouce_name)
        db_subnet_group.set_name(db_subnet_group_name)
        db_subnet_group.set_description('DB subnet group for %s-%s' % (vpc_name, env))
        db_subnet_group.set_default_output()
        db_subnet_groups.append(db_subnet_group)

        cache_subnet_group_resouce_name = '%s%sCacheSubnetGroup' % (vpc_name.capitalize(), env.capitalize())
        cache_subnet_group_name = '%s-%s-cache-subnet-group' % (vpc_name, env)
        cache_subnet_group = CacheSubnetGroup(cache_subnet_group_resouce_name)
        cache_subnet_group.set_name(cache_subnet_group_name)
        cache_subnet_group.set_description('Cache subnet group for %s-%s' % (vpc_name, env))
        cache_subnet_group.set_default_output()
        cache_subnet_groups.append(cache_subnet_group)

        for f in function_zones:
            route_table_resouce_name = '%s%sRouteTable' % (env.capitalize(), f.capitalize())
            route_table_name = '%s-%s-%s' % (vpc_name, env, f)
            route_table = RouteTable(route_table_resouce_name)
            route_table.set_name(route_table_name)
            route_table.set_vpc(vpc)
            route_table.set_default_output()
            route_tables.append(route_table)

            if f == 'pub':
                route_table.set_internet_gateway(gateway)

            for zone in availability_zones:
                subnet_resource_name = '%s%s%sSubnet' % (env.capitalize(), f.capitalize(), zone[-1].upper())
                subnet_name = '%s-%s-%s%s' % (vpc_name, env, f, zone[-1].upper())
                subnet = Subnet(subnet_resource_name)
                subnet.set_availability_zone(zone)
                subnet.set_name(subnet_name)
                subnet.set_vpc(vpc)
                subnet.set_default_output()
                subnets.append(subnet)

                route_table.subnet_associate(subnet)

                if f == 'pri':
                    db_subnet_group.add_subnet(subnet)
                    cache_subnet_group.add_subnet(subnet)

                print('%s  %s  %s: %s' % (env, f, zone, subnet_cidrblocks[cnt]))
                cnt += 1
        # print an empty line
        print('')

    security_group_tecotec = SecurityGroup('FromTecotecSecurityGroup')

    vpc_endpoint = VPCEndpoint('S3EndPoint')

    db_parameter_group = DBParameterGroup('DBParameterGroup')
    db_cluster_parameter_group = DBClusterParameterGroup('DBClusterParameterGroup')

    memcached_parameter_group = CacheParameterGroup('MemcachedParameterGroup')
    redis_parameter_group = CacheParameterGroup('RedisParameterGroup')

    vpc.set_name(vpc_name)
    vpc.set_network(vpc_cidrblock)
    vpc.set_default_output()

    gateway.set_name('%s-igw' % vpc_name)
    gateway.vpc_attach(vpc)
    gateway.set_default_output()

    for i in range(len(subnets)):
        subnets[i].set_cidrblock(subnet_cidrblocks[i])

    security_group_tecotec.set_name('%s-from-tecotec' % vpc_name)
    security_group_tecotec.set_description('Allow access from tecotec and tecogit')
    security_group_tecotec.add_ingress_rule('124.33.169.34/32', description='office main ip')
    security_group_tecotec.add_ingress_rule('210.138.216.179/32', description='office sub ip')
    security_group_tecotec.add_ingress_rule('210.140.160.39/32', protocal='tcp', from_port=22, to_port=22, description='server ip of teiden')
    security_group_tecotec.add_ingress_rule('210.140.164.140/32', protocal='tcp', from_port=443, to_port=443, description='server ip of git')
    security_group_tecotec.set_vpc(vpc)
    security_group_tecotec.set_default_output()

    vpc_endpoint.set_vpc(vpc)
    vpc_endpoint.set_service_name('com.amazonaws.%s.s3' % region)
    vpc_endpoint.set_endpoint_type('Gateway')
    vpc_endpoint.set_route_tables(route_tables)
    vpc_endpoint.set_default_output()

    db_parameter_group.set_name('teco.aurora-mysql5.7')
    db_parameter_group.set_description('Teco default parameter group for aurora-mysql5.7')
    db_parameter_group.set_family('aurora-mysql5.7')
    db_parameter_group.update_parameters({'general_log':1, 'internal_tmp_disk_storage_engine':'MYISAM', 'long_query_time':1, 'slow_query_log':1})
    db_parameter_group.set_default_output()

    db_cluster_parameter_group.set_name('teco.aurora-mysql5.7-cluster')
    db_cluster_parameter_group.set_description('Teco default cluster parameter group for aurora-mysql5.7')
    db_cluster_parameter_group.set_family('aurora-mysql5.7')
    db_cluster_parameter_group.update_parameters({'internal_tmp_disk_storage_engine':'MYISAM', 'server_audit_events':'CONNECT,QUERY,QUERY_DCL,QUERY_DDL,QUERY_DML,TABLE'})
    db_cluster_parameter_group.set_default_output()

    memcached_parameter_group.set_description('Teco default parameter group for memcached1.5')
    memcached_parameter_group.set_family('memcached1.5')
    memcached_parameter_group.set_default_output()

    redis_parameter_group.set_description('Teco default parameter group for redis5.0')
    redis_parameter_group.set_family('redis5.0')
    redis_parameter_group.set_default_output()

    resources = [vpc, gateway, security_group_tecotec, vpc_endpoint, db_parameter_group, db_cluster_parameter_group, memcached_parameter_group, redis_parameter_group]
    resources.extend(subnets)
    resources.extend(route_tables)
    resources.extend(security_groups)
    resources.extend(db_subnet_groups)
    resources.extend(cache_subnet_groups)

    template.add_resources(resources)

    with open(opts.output, mode='w') as f:
        f.write(template.to_json())

if __name__ == '__main__':
    main()
# -*- coding: utf-8 -*-

# legume. Copyright 2009-2011 Dale Reidy. All rights reserved.
# See LICENSE for details.

__docformat__ = 'restructuredtext'

'''
A message class is a subclass of legume.messages.BaseMessage with two
class attributes defined:

    * MessageTypeID - An integer uniquely identifying the message type. The
        allowed range for application messages is 1 to BASE_MESSAGETYPEID_SYSTEM-1.
    * MessageValues - A dictionary of the values stored within the message where
        the key is the name of the message value, and the value is the type.

Type names available for MessageValues:
    * 'int' - An integer
    * 'string n' - A string where n is the maximum string length, eg 'string 18'
    * 'float' - A double precision floating point.
    * 'bool' - A boolean (a 1 byte short)

An example message definition::

    class ChatMessage(legume.messages.BaseMessage):
        MessageTypeID = 1
        MessageValues = {
            'sender_name':'string 24',
            'message':'string 256',
            'channel':'string 24'
            }

    # Adding a message to a new message_factory
    message_factory = legume.messages.MessageFactory()
    message_factory.add(ChatMessage)

    # and/or add it to the global message factory
    legume.messages.message_factory.add(ChatMessage)

How to use this message definition::

    # Note how this client uses the packet_factory the
    # ChatMessage message was added to.
    client = legume.Client(packet_factory)

    # ..snip..

    # Create the message
    cm = ChatMessage()
    cm.sender_name.value = 'JoeUser'
    cm.message.value = 'This is a test message.'
    cm.channel.value = 'newbies'

    # send the message to the server
    client.send_message(cm)
'''

import struct
import logging
import string
from netshared import MessageError, PROTOCOL_VERSION

BASE_MESSAGETYPEID_SYSTEM = 1
BASE_MESSAGETYPEID_USER = 20

def isValidIdentifier(identifier):
    return not (' ' in identifier or identifier[0] not in string.ascii_letters)

class MessageValue(object):
    VALID_TYPE_NAMES = ['int', 'string', 'float', 'bool',
                        'uchar', 'char', 'short', 'varstring']

    def __init__(self, name, typename, value=None, max_length=None, message=None):
        '''
        Create a new packet type.

        The name parameter must be a valid python class attribute identifier.
        Typename can be one of 'int', 'string', 'float' or 'bool'.
        Value must be of the specified type.
        max_length is only required for string values.
        '''
        if not isValidIdentifier(name):
            raise MessageError, '%s is not a valid name' % name

        self.name = name
        self.typename = typename
        self._value = value
        self.max_length = max_length # only required for string

        if self.max_length is not None:
            self.max_length = int(self.max_length)

        if self.typename == 'string' and self.max_length is None:
            raise MessageError, 'String value requires a max_length attribute'
        elif self.max_length is not None and self.max_length < 1:
            raise MessageError, 'Max length must be None or > 0'
        elif self.typename not in self.VALID_TYPE_NAMES:
            raise MessageError, '%s is not a valid type name' % self.typename
        elif self.name == '':
            raise MessageError('A value name is required')

        if message is not None and message.UseDefaultValues:
            self.set_default_value()

    def set_default_value(self):
        if self.typename == 'int':
            self._value =0
        elif self.typename == 'short':
            self._value = 0
        elif self.typename == 'string':
            self._value = ""
        elif self.typename == 'varstring':
            self._value = ""
        elif self.typename == 'float':
            self._value = 0.0
        elif self.typename == 'bool':
            self._value = False
        elif self.typename == 'uchar':
            self._value = ""
        else:
            raise MessageError, ('Cant set default value for type "%s"' %
                self.typename)

    def get_message_values(self):
        if self.typename == 'varstring':
            return [len(self.value), self._value]
        else:
            return [self._value]

    def get_value(self):
        return self._value

    def set_value(self, value):
        if self.typename == 'string':
            if len(value) > self.max_length:
                raise MessageError, 'String value is too long.'
            self._value = value.replace('\0', '')
        else:
            self._value = value

    value = property(get_value, set_value)

    def get_format_string(self):
        '''
        Returns the string necessary for encoding this value using struct.
        '''
        if self.typename == 'int':
            return 'i'

        elif self.typename == 'short':
            return 'H'

        elif self.typename == 'string':
            return str(self.max_length)+'s'

        elif self.typename == 'float':
            return 'd'

        elif self.typename == 'bool':
            return 'b'

        elif self.typename == 'varstring':
            return 'H'+str(len(self._value))+'s'

        elif self.typename == 'uchar':
            return 'B'

        else:
            raise MessageError, ('Cant get format string for type "%s"' %
                self.typename)

    def read_from_byte_buffer(self, byteBuffer):
        if self.typename == 'int':
            self._value = byteBuffer.read_struct('i')[0]

        elif self.typename == 'short':
            self._value = byteBuffer.read_struct('H')[0]

        elif self.typename == 'string':
            self._value = byteBuffer.read_struct(str(self.max_length)+'s')[0]
            self._value = self._value.replace('\0', '')

        elif self.typename == 'float':
            self._value = byteBuffer.read_struct('d')[0]

        elif self.typename == 'bool':
            self._value = byteBuffer.read_struct('b')[0]

        elif self.typename == 'varstring':
            length = byteBuffer.read_struct('H')[0]
            self._value = byteBuffer.read_struct(str(length)+'s')[0]

        elif self.typename == 'uchar':
            self._value = byteBuffer.read_struct('B')[0]

        else:
            raise MessageError, ('Cant get read from byteBuffer for type "%s"' %
                self.typename)

class BaseMessage(object):
    '''
    Data packets must inherit from this base class. A subclass must have a
    static property called MessageTypeID set to a integer value to uniquely
    identify the packet within a single PacketFactory.
    '''

    HEADER_FORMAT = 'B'
    MessageTypeID = None
    MessageValues = None
    UseDefaultValues = True
    _log = logging.getLogger('legume.BaseMessage')

    def __init__(self, *values):
        self._message_type_id = self.MessageTypeID
        if self.MessageTypeID is None:
            raise MessageError('%s does not have a MessageTypeID' %
                self.__class__.__name__)

        self.value_names = []

        if len(values) > 0:
            for value in values:
                self._add_value(value)
        elif self.MessageValues is not None:
            for mvname, mvtype in self.MessageValues.iteritems():
                if mvtype[:6] == 'string':
                    valuetype, param = mvtype.split(' ')
                else:
                    valuetype = mvtype
                    param = None
                new_value = MessageValue(mvname, valuetype, None, param, self)
                self._add_value(new_value)

        self.set_message_values_to_defaults()

    def _add_value(self, value):
        self.value_names.append(value.name)
        self.__dict__[value.name] = value

    def get_header_format(self):
        '''
        Returns the header format as a struct compatible string.
        '''
        return self.HEADER_FORMAT

    def get_header_values(self):
        '''
        Returns a list containing the values used to construct
        the packet header.
        '''
        return [self._message_type_id]

    def get_data_format(self):
        '''
        Returns a struct compatible format string of the packet data
        '''
        format = []
        for valuename in self.value_names:
            value = self.__dict__[valuename]
            if not isinstance(value, MessageValue):
                raise MessageError(
                    'Overwritten message value! Use msgval.value = xyz')
            format.append(value.get_format_string())
        return ''.join(format)

    def get_message_values(self):
        '''
        Returns a list containing the header+packet values used
        to construct the packet
        '''
        values = self.get_header_values()
        for name in self.value_names:
            self._log.debug('Packet value %s = %s' %
                (name, self.__dict__[name].get_message_values()))
            values.extend(self.__dict__[name].get_message_values())
        self._log.debug('Packetvalues = %s' % values)
        return values

    def get_message_format(self):
        '''
        Returns a struct compatible format string of the message
        header and data
        '''
        return self.get_header_format() + self.get_data_format()

    def get_packet_bytes(self):
        '''
        Returns a string containing the header and data. This
        string can be passed to .loadFromString(...).
        '''

        message_values = self.get_message_values()

        packet_bytes = struct.pack(
            '!'+self.get_message_format(),
            *message_values)

        self._log.debug('MESSAGE STRING LENGTH=%s' % len(packet_bytes))

        return packet_bytes

    @staticmethod
    def read_header_from_byte_buffer(byteBuffer):
        '''
        Read a packet header from an instance of ByteBuffer. This
        method will return a tuple containing the header
        values.
        '''
        return byteBuffer.read_struct(BaseMessage.HEADER_FORMAT)

    def set_message_values_to_defaults(self):
        '''
        Override this method to assign default values.
        '''
        pass

    def read_from_byte_buffer(self, byteBuffer):
        '''
        Reconstitute the packet from a ByteBuffer instance
        '''
        for name in self.value_names:
            self.__dict__[name].read_from_byte_buffer(byteBuffer)

class ConnectRequest(BaseMessage):
    '''
    A connection request packet - sent by a client to the server.
    '''
    MessageTypeID = BASE_MESSAGETYPEID_SYSTEM+1
    MessageValues = {
        'protocol':'uchar'
    }

    def load_default_values(self):
        self.protocol.value = PROTOCOL_VERSION


class ConnectRequestRejected(BaseMessage):
    '''
    A connection request rejection packet - sent by the server back to
    a client.
    '''
    MessageTypeID = BASE_MESSAGETYPEID_SYSTEM+2

class ConnectRequestAccepted(BaseMessage):
    '''
    A connection request accepted packet - sent by the server back to
    a client.
    '''
    MessageTypeID = BASE_MESSAGETYPEID_SYSTEM+3

class KeepAliveRequest(BaseMessage):
    '''
    This is sent by the server to keep the connection alive.
    '''
    MessageTypeID = BASE_MESSAGETYPEID_SYSTEM+4
    MessageValues = {
        'id':'short'
    }

class KeepAliveResponse(BaseMessage):
    '''
    A clients response to the receipt of a KeepAliveRequest message.
    '''
    MessageTypeID = BASE_MESSAGETYPEID_SYSTEM+5
    MessageValues = {
        'id':'short'
    }

class Disconnected(BaseMessage):
    '''
    This message is sent by either the client or server to indicate to the
    other end of the connection that the link is closed. In cases where
    the connection is severed due to software crash, this message will
    not be sent, and the socket will eventually disconnect due to a timeout.
    '''
    MessageTypeID = BASE_MESSAGETYPEID_SYSTEM+6

class MessageAck(BaseMessage):
    '''
    Sent by either a client or server to acknowledge receipt of an
    in-order or reliable message.
    '''
    MessageTypeID = BASE_MESSAGETYPEID_SYSTEM+7
    MessageValues = {
        'message_to_ack':'int'
    }

class Ping(BaseMessage):
    MessageTypeID = BASE_MESSAGETYPEID_SYSTEM+8
    MessageValues = {
        'id':'short'
    }

class Pong(BaseMessage):
    MessageTypeID = BASE_MESSAGETYPEID_SYSTEM+9
    MessageValues = {
        'id':'short'
    }

class MessageFactoryItem(object):
    def __init__(self, message_name, message_type_id, message_factory):
        self.message_name = message_name
        self.message_type_id = message_type_id
        self.message_factory = message_factory

class MessageFactory(object):
    def __init__(self):
        self._factories_by_name = {}
        self._factories_by_id = {}

        self.add(*messages.values())

    def add(self, *message_classes):
        '''
        Add message class(es) to the message factory.
        The parameters to this method must be subclasses of BaseMessage.

        A MessageError will be raised if a message already exists in
        this factory with an identical name or MessageTypeID.
        '''
        for message_class in message_classes:
            if message_class.__name__ in self._factories_by_name:
                raise MessageError, 'Message type already in factory'
            if message_class.MessageTypeID in self._factories_by_id:
                raise MessageError, 'message %s has same Id as message %s' % (
                    message_class.__name__,
                    self._factories_by_id[
                      message_class.MessageTypeID].message_name)
            messsage_factory_item = MessageFactoryItem(
                message_class.__name__,
                message_class.MessageTypeID,
                message_class)
            self._factories_by_name[message_class.__name__] = messsage_factory_item
            self._factories_by_id[message_class.MessageTypeID] = messsage_factory_item

    def get_by_id(self, id):
        '''
        Obtain a message class by specifying the packets MessageTypeID.
        If the message cannot be found a MessageError exception is raised.
        '''
        try:
            return self._factories_by_id[id].message_factory
        except KeyError, e:
            raise MessageError, 'No message exists with ID %s' % str(id)

    def get_by_name(self, name):
        '''
        Obtain a message class by specifying the packets name.
        If the message cannot be found a MessageError exception is raised.
        '''
        try:
            return self._factories_by_name[name].message_factory
        except KeyError, e:
            raise MessageError, 'No message exists with name %s' % str(name)

    def is_a(self, message_instance, message_name):
        '''
        Determine if message_instance is an instance of the named message class.

        Example:
        >>> tp = TestPacket1()
        >>> message_factory.is_a(tp, 'TestPacket1')
        True
        '''
        return isinstance(message_instance, self.get_by_name(message_name))

messages = {
    'ConnectRequest':ConnectRequest,
    'ConnectRequestRejected':ConnectRequestRejected,
    'ConnectRequestAccepted':ConnectRequestAccepted,
    'KeepAliveRequest':KeepAliveRequest,
    'KeepAliveResponse':KeepAliveResponse,
    'Disconnected':Disconnected,
    'MessageAck':MessageAck,
    'Pong':Pong,
    'Ping':Ping
}

# The default global packet factory.
message_factory = MessageFactory()
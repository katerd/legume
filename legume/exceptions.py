class LegumeError(Exception): pass
class ArgumentError(LegumeError): pass
class NetworkEndpointError(LegumeError): pass
class PacketDataError(LegumeError): pass
class ServerError(LegumeError): pass
class ClientError(Exception): pass
class MessageError(LegumeError): pass

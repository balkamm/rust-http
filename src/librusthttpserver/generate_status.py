# These are taken from http://en.wikipedia.org/wiki/List_of_HTTP_Status_Codes.
# Last updated on 2013-07-04
# Entries from third-party vendors not standardised upon are not included.
# If not specified otherwise, they are defined in RFC 2616.

from collections import namedtuple

# Yes, this is ugly code.
# No, I don't mind.
# That was easy. :-)

longest_ident = 0

class Entry(namedtuple('Entry', ('ident', 'code', 'reason', 'note'))):
    def padded_ident(self, suffix=''):
        return (self.ident + suffix).ljust(longest_ident + len(suffix))

simple_data = (
        '1xx Informational',
        (100, "Continue"),
        (101, "Switching Protocols"),
        (102, "Processing", "WebDAV; RFC 2518"),

        '2xx Success',
        (200, "OK"),
        (201, "Created"),
        (202, "Accepted"),
        (203, "Non-Authoritative Information", "since HTTP/1.1"),
        (204, "No Content"),
        (205, "Reset Content"),
        (206, "Partial Content"),
        (207, "Multi-Status", "WebDAV; RFC 4918"),
        (208, "Already Reported", "WebDAV; RFC 5842"),
        (226, "IM Used", "RFC 3229"),

        '3xx Redirection',
        (300, "Multiple Choices"),
        (301, "Moved Permanently"),
        (302, "Found"),
        (303, "See Other", "since HTTP/1.1"),
        (304, "Not Modified"),
        (305, "Use Proxy", "since HTTP/1.1"),
        (306, "Switch Proxy"),
        (307, "Temporary Redirect", "since HTTP/1.1"),
        (308, "Permanent Redirect", "approved as experimental RFC: http://tools.ietf.org/html/draft-reschke-http-status-308"),

        '4xx Client Error',
        (400, "Bad Request"),
        (401, "Unauthorized"),
        (402, "Payment Required"),
        (403, "Forbidden"),
        (404, "Not Found"),
        (405, "Method Not Allowed"),
        (406, "Not Acceptable"),
        (407, "Proxy Authentication Required"),
        (408, "Request Timeout"),
        (409, "Conflict"),
        (410, "Gone"),
        (411, "Length Required"),
        (412, "Precondition Failed"),
        (413, "Request Entity Too Large"),
        (414, "Request-URI Too Long"),
        (415, "Unsupported Media Type"),
        (416, "Requested Range Not Satisfiable"),
        (417, "Expectation Failed"),
        (418, "I'm a teapot", "RFC 2324"),
        (419, "Authentication Timeout"),
        (422, "Unprocessable Entity", "WebDAV; RFC 4918"),
        (423, "Locked", "WebDAV; RFC 4918"),
        (424, "Failed Dependency", "WebDAV; RFC 4918"),
        (424, "Method Failure", "WebDAV"),
        (425, "Unordered Collection", "Internet draft"),
        (426, "Upgrade Required", "RFC 2817"),
        (428, "Precondition Required", "RFC 6585"),
        (429, "Too Many Requests", "RFC 6585"),
        (431, "Request Header Fields Too Large", "RFC 6585"),
        (451, "Unavailable For Legal Reasons", "Internet draft"),

        '5xx Server Error',
        (500, "Internal Server Error"),
        (501, "Not Implemented"),
        (502, "Bad Gateway"),
        (503, "Service Unavailable"),
        (504, "Gateway Timeout"),
        (505, "HTTP Version Not Supported"),
        (506, "Variant Also Negotiates", "RFC 2295"),
        (507, "Insufficient Storage", "WebDAV; RFC 4918"),
        (508, "Loop Detected", "WebDAV; RFC 5842"),
        (510, "Not Extended", "RFC 2774"),
        (511, "Network Authentication Required", "RFC 6585"),
        )


def camel_case(msg):
    '''
    >>> camel_case("I'm a Tea-pot")
    'ImATeaPot'
    '''
    return ''.join(word.capitalize()
            for word in msg.replace('-', ' ').replace("'", '').split())

def make_entry(raw_entry):
    global longest_ident
    if isinstance(raw_entry, tuple):
        # Format: (code, reason[, note])
        code = raw_entry[0]
        reason = raw_entry[1]
        note = None if len(raw_entry) == 2 else raw_entry[2]
        ident = camel_case(reason)
        longest_ident = max(longest_ident, len(ident))
        return Entry(ident, code, reason, note)
    else:
        return raw_entry


data = tuple(make_entry(raw_entry) for raw_entry in simple_data)


def main():
    with open('status.rs', 'w') as out:
        out.write('''// DO NOT MODIFY THIS FILE DIRECTLY. It is generated by generate_status.py.

use std::num::IntConvertible;

/// HTTP status code
pub enum Status {
''')
        for entry in data:
            if isinstance(entry, Entry):
                if entry.note is None:
                    out.write('    %s,\n' % entry.ident)
                else:
                    out.write('    %s,  // %s\n' % (entry.ident, entry.note))
            else:
                out.write('\n    // %s\n' % entry)

        out.write('''
    UnregisteredStatusCode(u16, ~str),
}

impl Status {

    pub fn new(code: u16, reason: ~str) -> Status {
        UnregisteredStatusCode(code, reason)
    }

    /// Get the status code
    pub fn code(&self) -> u16 {
        match *self {
''')
        for entry in data:
            if isinstance(entry, Entry):
                out.write('            %s => %d,\n' % (entry.padded_ident(), entry.code))
            else:
                out.write('\n            // %s\n' % entry)
        out.write('''
            UnregisteredStatusCode(code, _) => code,
        }
    }

    /// Get the reason phrase
    pub fn reason(&self) -> ~str {
        match *self {
''')
        for entry in data:
            if isinstance(entry, Entry):
                out.write('            %s => ~"%s",\n' % (entry.padded_ident(), entry.reason))
            else:
                out.write('\n            // %s\n' % entry)
        out.write('''
            UnregisteredStatusCode(_, ref reason) => (*reason).clone(),
        }
    }
}

impl ToStr for Status {
    /// Produce the HTTP status message incorporating both code and message,
    /// e.g. `ImATeapot.to_str() == "418 I'm a teapot"`
	pub fn to_str(&self) -> ~str {
		fmt!("%? %s", self.code(), self.reason())
	}
}

impl IntConvertible for Status {

    /// Equivalent to `self.code()`
    pub fn to_int(&self) -> int {
        self.code() as int
    }

    /// Get a *registered* status code from the number of its status code.
    ///
    /// This will fail if an unknown code is passed.
    ///
    /// For example, `from_int(200)` will return `OK`.
    pub fn from_int(n: int) -> Status {
        match n {
''')
        matched_numbers = set()
        for entry in data:
            if isinstance(entry, Entry):
                if entry.code in matched_numbers:
                    # Purpose: FailedDependency and MethodFailure both use 424,
                    # but clearly they mustn't both go in here
                    continue
                out.write('            %d => %s,\n' % (entry.code, entry.ident))
                matched_numbers.add(entry.code)
            else:
                out.write('\n            // %s\n' % entry)
        out.write('''
            _   => { fail!(fmt!("No registered HTTP status code %d", n)); }
        }
    }
}''')


if __name__ == '__main__':
    main()

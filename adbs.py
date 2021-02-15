import struct
import os
from typing import BinaryIO, Any, Dict


class ADBSDeserializer:
    def __init__(self, f: BinaryIO):
        self.f = f
        magic, self.version, dic_offset = struct.unpack(
            '<4sHxxI', self.f.read(12))
        if magic != b'ADBS':
            raise ValueError('invalid magic')
        self.f.seek(dic_offset)
        self.dic = []
        while True:
            buf = self.f.read(2)
            if len(buf) != 2:
                break
            l, = struct.unpack('<H', buf)
            self.dic.append(self.f.read(l).decode('utf-16-le'))
        self.f.seek(12)

    def start_object(self, expected_name):
        if self.read_uint8() != 0xff:
            raise ValueError(
                'expecting object start at 0x{:x}'.format(self.f.tell()))
        dicid = self.read_uint8()
        name = self.dic[dicid]
        if expected_name != name:
            raise ValueError('expecting object {!r}, not {!r}, at 0x{:x}'.format(
                expected_name, name, self.f.tell()))

    def end_object(self):
        if self.read_uint8() != 0xfe:
            raise ValueError(
                'expecting object end at 0x{:x}'.format(self.f.tell()))

    def has_object(self):
        return self.peek_uint8() == 0xff

    def read_properties(self, prop_readers):
        properties = {}
        while self.peek_uint8() < 0xfd:
            dicid = self.read_uint16()
            name = self.dic[dicid]
            properties[name] = prop_readers[name]()
        return properties

    def peek_uint8(self):
        val = self.read_uint8()
        self.f.seek(-1, os.SEEK_CUR)
        return val

    def read_bytes(self):
        l, = struct.unpack('<I', self.f.read(4))
        return self.f.read(l)

    def read_str(self):
        return self.read_bytes().decode('utf-16-le')

    def read_ansi_str(self):
        return self.read_bytes().decode('iso-8859-15')

    def read_enum(self):
        return self.dic[self.read_uint16()]

    def read_uint8(self):
        val, = struct.unpack('<B', self.f.read(1))
        return val

    def read_uint16(self):
        val, = struct.unpack('<H', self.f.read(2))
        return val

    def read_uint32(self):
        val, = struct.unpack('<I', self.f.read(4))
        return val

    def read_uint64(self):
        val, = struct.unpack('<Q', self.f.read(8))
        return val

    def read_int32(self):
        val, = struct.unpack('<i', self.f.read(4))
        return val

    def read_bcd(self):
        l, = struct.unpack('<B', self.f.read(1))
        buf = self.f.read(l) + (34 - l)*b'\x00'
        # https://wiki.freepascal.org/BcdUnit
        precision = buf[0]
        sign = buf[1] >> 7
        decimals = buf[1] & 0x3f
        number = buf[2:].hex()
        number = number[:precision]
        number = number[:-decimals] + '.' + number[-decimals:]
        if sign == 1:
            number = '-' + number
        return number

    def read_currency(self):
        number = '{:04d}'.format(self.read_uint64())
        decimals = 4
        number = number[:-decimals] + '.' + number[-decimals:]
        return number


class TableDeserializer(ADBSDeserializer):
    def load(self):
        self.start_object('Manager')
        manager = self.read_properties({'UpdatesRegistry': self.read_uint8})

        self.start_object('TableList')
        table_list = []
        while self.has_object():
            self.start_object('Table')
            table: Dict[str, Any] = {'class': 'Table'}
            table.update(self.read_properties({
                'Name': self.read_str,
                'SourceName': self.read_str,
                'SourceID': self.read_uint32,
                'TabID': self.read_uint32,
                'EnforceConstraints': self.read_uint8,
                'MinimumCapacity': self.read_uint32,
                'CheckNotNull': self.read_uint8,
            }))
            self.start_object('ColumnList')
            column_list = []
            while self.has_object():
                self.start_object('Column')
                column = {'class': 'Column'}
                column.update(self.read_properties({
                    'Name': self.read_str,
                    'SourceName': self.read_str,
                    'SourceID': self.read_uint32,
                    'DataType': self.read_enum,
                    'Precision': self.read_uint32,
                    'Scale': self.read_uint32,
                    'Size': self.read_uint32,
                    'Searchable': self.read_uint8,
                    'AllowNull': self.read_uint8,
                    'ReadOnly': self.read_uint8,
                    'Default': self.read_uint8,
                    'BlobData': self.read_uint8,
                    'Virtual': self.read_uint8,
                    'Base': self.read_uint8,
                    'Expr': self.read_uint8,
                    'OAllowNull': self.read_uint8,
                    'OUnique': self.read_uint8,
                    'OReadOnly': self.read_uint8,
                    'OInUpdate': self.read_uint8,
                    'OInWhere': self.read_uint8,
                    'OInKey': self.read_uint8,
                    'OAfterInsChanged': self.read_uint8,
                    'OAfterUpdChanged': self.read_uint8,
                    'OriginColName': self.read_str,
                    'OriginTabName': self.read_str,
                    'SourcePrecision': self.read_uint32,
                    'SourceScale': self.read_uint32,
                    'SourceSize': self.read_uint32,
                }))
                column_list.append(column)
                self.end_object()  # Column
            table['ColumnList'] = column_list
            self.end_object()  # ColumnList

            self.start_object('ConstraintList')
            table['ConstraintList'] = []
            self.end_object()  # ConstraintList

            self.start_object('ViewList')
            table['ViewList'] = []
            self.end_object()  # ViewList

            self.start_object('RowList')
            row_list = []
            while self.has_object():
                self.start_object('Row')
                row = self.read_properties({
                    'RowID': self.read_uint32,
                    'RowPriorState': self.read_enum,
                })

                self.start_object('Original')
                original = {}
                while self.peek_uint8() < 0xfd:
                    readers = {
                        'dtBlob': self.read_bytes,
                        'dtInt32': self.read_int32,
                        'dtAnsiString': self.read_ansi_str,
                        'dtFmtBCD': self.read_bcd,
                        'dtCurrency': self.read_currency,
                    }
                    column_id = self.read_uint16()
                    column = column_list[column_id]
                    dtype = column['DataType']
                    name = column['Name']
                    value = readers[dtype]()
                    original[name] = value
                row['Original'] = original
                self.end_object()  # Original

                row_list.append(row)
                self.end_object()  # Row
            table['RowList'] = row_list
            self.end_object()  # RowList

            table_list.append(table)
            self.end_object()  # Table
        manager['TableList'] = table_list
        self.end_object()  # TableList

        self.start_object('RelationList')
        manager['RelationList'] = []
        self.end_object()  # RelationList

        self.start_object('UpdatesJournal')
        updates_journal = self.read_properties({'SavePoint': self.read_uint32})
        self.start_object('Changes')
        updates_journal['Changes'] = []
        self.end_object()  # Changes
        self.end_object()  # UpdatesJournal

        self.end_object()  # Manager

        root = {'FDBS': {'Version': self.version, 'Manager': manager}}
        return root

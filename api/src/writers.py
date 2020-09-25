import csv
from itertools import chain

from django.http import HttpResponse, StreamingHttpResponse


class CSVBuffer:
    """An object that implements just the write method of the file-like
    interface.
    """

    def write(self, value):
        """Return the string to write."""
        return value


class CSVExport:
    """Class to (download) an iterator to a
    CSV file."""

    def export(self, filename, iterator, serializer=None, header=None, streaming=False):
        # 1. Create our writer object with the pseudo buffer
        writer = csv.writer(CSVBuffer())

        if not header:
            header = iterator[0].keys()

        if not serializer:
            serializer = lambda x: x.values()

        # 2. Create the HttpResponse using our iterator as content
        cls = StreamingHttpResponse if streaming else HttpResponse

        response = cls(
            chain(
                (writer.writerow(col for col in header)),
                (writer.writerow(serializer(data)) for data in iterator if data),
            ),
            content_type="text/csv",
        )

        # 3. Add additional headers to the response
        response['Content-Disposition'] = f"attachment; filename={filename}.csv"
        # 4. Return the response
        return response

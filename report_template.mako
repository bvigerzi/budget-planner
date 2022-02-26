<h1>${header}</h1>

<table rules="none">
    ${makerow(rows_header, True)}
    % for row in rows:
        ${makerow(row, False)}
    % endfor
</table>

<%def name="makerow(row, header)">
    % if row[0] == "Total" or header:
        <tr style="border: 1px solid black">
    % else:
        <tr>
    % endif
    % for name in row:
        % if header == True:
            <th align="right" style="padding-right:20px">${name}</th>
        % else:
            % if loop.last:
                % if name != "" and float(name) >= 0:
                    <td align="right" style="padding-right:20px" bgcolor="green">${name}</td>
                % elif name != "":
                    <td align="right" style="padding-right:20px" bgcolor="red">${name}</td>
                % else:
                    <td align="right" style="padding-right:20px">${name}</td>
                % endif
            % else:
                <td align="right" style="padding-right:20px">${name}</td>
            % endif
        % endif
    % endfor
    </tr>
</%def>

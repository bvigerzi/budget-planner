<style>
td {
    padding-right: 20px;
}
th {
    padding-right: 20px;
}
.negative {
    border: 1px solid #F00;
}
.positive {
    border: 1px solid #0F0;
}
.bold {
    font-weight: bold;
}
</style>
<h1>${header}</h1>

<table rules="none">
    ${makerow(rows_header, True)}
    % for row in rows:
        ${makerow(row, False)}
    % endfor
    <tr></tr>
</table>

<%def name="computeClass(row, name, index)">
    <%
        colour_modifier = ""
        weight_modifier = ""
        if row[0] == "Total" or row[0] == "Complete Total":
            weight_modifier = "bold"
        if index > 2 and index != 5:
            if name != "" and float(name) > 0:
                colour_modifier = "positive"
            elif name != "" and float(name) < 0:
                colour_modifier = "negative"
    %>
    "${colour_modifier} ${weight_modifier}"
</%def>

<%def name="makerow(row, header)">
    % if row[0] == "Total" or row[0] == "Complete Total" or header:
        <tr style="border: 1px solid black">
    % else:
        <tr>
    % endif
    % for name in row:
        % if header == True:
            <th align="right">${name}</th>
        % else:
            <td align="right" class=${computeClass(row, name, loop.index)}>${name}</td>
        % endif
    % endfor
    </tr>
</%def>

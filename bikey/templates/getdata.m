function output = getdata
    write(client, "hello there!", "string");
    data = readline(client);
    output = 0;
    output = str2double(data);
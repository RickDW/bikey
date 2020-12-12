function output = getdata(port)
    persistent client
    if isempty(client)
        client = tcpclient('127.0.0.1', port, "Timeout", 10*60); % a full minute long timeout just to be sure
    end
    
    write(client, "some message", "string");
    data = readline(client);
    
    output = str2double(data);
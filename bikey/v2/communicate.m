function action = communicate(port, observation)
    persistent client % use one client for one simulation
    if isempty(client)
        client = tcpclient("127.0.0.1", port, "Timeout", 10*60); % a minute long timeout just to be sure
    end

    message = convertCharsToStrings(jsonencode(observation));
    terminator = "\n";
    write(client, message + terminator, "string");
    flush(client);

    action = [0; 0; 0];
    action = str2double(jsondecode(readline(client)));
end
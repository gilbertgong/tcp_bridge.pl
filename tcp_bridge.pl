#!/usr/bin/perl

use IO::Socket::INET;
# use Time::HiRes;

# default conf
my $port=4243;
my $listen_ip="127.0.0.1";
my $opt_strip_put=1;

# probably don't need to change these
# auto-flush on socket
my $autoflush = 1;
my $listen_queue = 10;

# internal metrics
my $m_namespace = "tcp_bridge.agent.";
my $m_lines_read = 0;
my $m_connections_processed = 0;
my $m_delay = 15;
my $m_last = 0;
my $m_ptime = 0;

# creating a listener
my $listener = new IO::Socket::INET (
    LocalHost => $listen_ip,
    LocalPort => $port,
    Proto => 'tcp',
    Listen => $listen_queue,
    Reuse => 1
    );
die "cannot create listener $!\n" unless $listener;
$listener->autoflush($autoflush);
#print "server waiting for client connection on port $port\n";

sub strip_put {
   my $line = shift;
    # if not enabled, just return unchanged
    if (!$opt_strip_put) {
	return $line;
    }

   if ($line =~ /^put /) {
       $line = substr ($line, 4);
    }
    return $line;
}

sub handle_client {
    my $client_socket = shift;

#    my $start = Time::HiRes::time();
    # read until connection closed
    my $line = "";
    while ($line = $client_socket->getline()) {
	# and print to stdout
	$line = strip_put ($line);
	print ($line);
	$m_lines_read++;
    }

    # other side closed connection, now we close our side
    shutdown($client_socket, 1);

#    my $end = Time::HiRes::time();
#    $m_ptime += ($end - $start);
    $m_connections_processed++;
}

sub print_my_metrics {
    my $ts = time();
    if ($ts > $m_last + $m_delay) {
	print ($m_namespace . "lines_read $ts $m_lines_read\n");
	print ($m_namespace . "connections_processed $ts $m_connections_processed\n");
#	print ($m_namespace . "processing_time $ts $m_ptime\n");
	print ($m_namespace . "active $ts 1\n");
    }
    $m_last = $ts;
}

##### main loop
while(1) {
    my $client = $listener->accept();
    handle_client ($client);
    print_my_metrics();
}
 
$listener->close();

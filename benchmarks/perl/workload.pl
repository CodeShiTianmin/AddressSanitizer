# Text-processing workload in the spirit of 400.perlbench (mail filtering / diff):
# regex scanning, hash-based word statistics, string rewriting, sorting, sprintf.
# (no "use strict": miniperl runs without the module library)
my ($file) = @ARGV;
open(my $fh, '<', $file) or die "open $file: $!";
my @lines = <$fh>; close $fh;
my (%freq, %bigram, $chk);
for my $pass (1 .. 4) {
  my $prev = '';
  for my $l (@lines) {
    my $s = $l;
    $s =~ s/\s+$//;
    $s =~ s/([A-Z]<)([^>]*)>/$2/g;            # strip POD formatting codes
    $s =~ tr/A-Z/a-z/;
    for my $w ($s =~ /([a-z_][a-z0-9_]{2,})/g) {
      $freq{$w}++;
      $bigram{"$prev $w"}++ if $prev ne '';
      $prev = $w;
    }
    $chk++ if $s =~ /(?:malloc|free|realloc)\s*\(/;
    $chk++ if $s =~ /^\s*(?:sub|my|our)\s+\$?\w+/;
    my $r = reverse $s; $chk += length($r) & 7;
  }
}
my @top = (sort { $freq{$b} <=> $freq{$a} || $a cmp $b } keys %freq)[0 .. 49];
my @topb = (sort { $bigram{$b} <=> $bigram{$a} || $a cmp $b } keys %bigram)[0 .. 49];
my $out = '';
$out .= sprintf("%-24s %8d\n", $_, $freq{$_}) for @top;
$out .= sprintf("%-40s %8d\n", $_, $bigram{$_}) for @topb;
my @parts = split /\n/, $out;
my $joined = join('|', map { ucfirst } @parts);
printf "words=%d bigrams=%d chk=%d len=%d\n%s", scalar(keys %freq), scalar(keys %bigram), $chk, length $joined, $out;

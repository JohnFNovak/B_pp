@@GUIDE
@Passes = 2
@Verbose = 4
GUIDE@@

@@TEMPLATE
%list.txt%

@list.num@

@list2.letter@

!@num@
TEMPLATE@@

Testing

@@ITERABLES
@list(num):
1
2
3
ITERABLES@@

@@FORMS
FORMS@@

@@!REFERENCES
@num:
Number
!REFERENCES@@

@@ITERABLES
@list2(letter):
a
b
c
ITERABLES@@
# 

OBJS = wv.o

wv_wrap.a:	$(OBJS)
	-rm wv.a
	ar rcs libwv.a $(OBJS)
	$(RANLB)

$(OBJS): wv.h

.c.o:
	gcc -c $(COPTS) -DLWS_NO_FORK  $< 


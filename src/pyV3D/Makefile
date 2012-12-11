# 

OBJS = wv.o

wv_wrap.a:	$(OBJS)
	-rm wv.a
	ar wv.a $(OBJS)
	$(RANLB)

$(OBJS): wsss.h

.c.o:
	gcc -c $(COPTS) -DLWS_NO_FORK  $< 


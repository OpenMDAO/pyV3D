# 

OBJS = wv.o

wv_wrap.a:	$(OBJS)
	-rm libwv.a
	ar rcs libwv.a $(OBJS)
	$(RANLB)

$(OBJS): wv.h

.c.o:
	gcc -c $(COPTS) -fPIC -DLWS_NO_FORK  $< 


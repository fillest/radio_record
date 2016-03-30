import traceback
quiet_exit = False
class QuietExit (Exception): pass
try:


	import subprocess
	import threading
	import datetime
	import glob
	import os
	import sys
	import signal
	import ctypes
	import time
	import shlex


	#TODO config
	#TODO pin to numbers (numbers get strongly remembered)
	streams = [
		('jungletrain', 'http://stream2.jungletrain.net:8000/', 'mp3'),
		('subfm',       'http://listen.sub.fm/hi', 'mp3'),
		('dubstepfm',   'http://relay1.dubstep.fm/', 'aac'),
		('motttfm',     'http://stream.mottt.fm:9092/', 'mp3'),
		('mhyh',        'http://50.7.98.106:8830/stream', 'mp3'),
		('hoxtonfm',    'http://95.142.158.105:8024/stream', 'mp3'),
		('psychoradio', 'http://stream.psychoradio.org:8000/', 'mp3'),
		('rinsefm',     'http://r3.dgen.net:8000/rinseradio', 'mp3'),
		('kexp',        'http://live-aacplus-64.kexp.org/kexp64.aac', 'aac'),
	]
	mplayer_fpath = 'C:/apps/mplayer/mplayer.exe' 
	dump_dirpath = 'c:/radio_stream_dumps'


	def fnow ():
		return datetime.datetime.utcnow().strftime('%Y.%m.%d_%H-%M-%SUTC')  #':' is invalid on windows

	must_stop_mplayer = [False]
	mplayer_exited = [False]

	def mplayer_io (info_fpath, mplayer_proc):
		#TODO handle exceptions
		with open(info_fpath, 'wb') as f_info:
			while True:
				line = mplayer_proc.stdout.readline()
				if not line:
					retcode = mplayer_proc.poll()
					is_running = retcode is None
					if not is_running:
						print "@@@ mplayer exited with %s" % retcode
						mplayer_exited[0] = True
						break

				line = line.rstrip()
				if not line.endswith('bytes written'):
					l = "%s %s\n" % (fnow(), line)
					print l,
					f_info.write(l)
					f_info.flush()

				if must_stop_mplayer[0]:
					#http://stackoverflow.com/a/7980368/1183239
					# os.kill(0, signal.CTRL_C_EVENT)
					#TODO don't need to do it async no more?
					ctypes.windll.kernel32.GenerateConsoleCtrlEvent(signal.CTRL_C_EVENT, 0)
					must_stop_mplayer[0] = False

	def start_recording (sname, stream_url, ext):
		nows = fnow()

		dump_fpath = '%s/stream_%s_%s.%s' % (dump_dirpath, nows, sname, ext)
		info_fpath = '%s/stream_%s_%s_info.txt' % (dump_dirpath, nows, sname)

		cmd = ('%s -dumpstream -dumpfile %s '
			'-quiet -priority abovenormal -nofontconfig -noautosub -loop 0 -noar -noconsolecontrols -nolirc -nojoystick -nomouseinput -prefer-ipv4 '
			'%s'
			% (mplayer_fpath, dump_fpath, stream_url))
		# cmd = mplayer_fpath
		cmd = shlex.split(cmd)
		proc = subprocess.Popen(cmd, shell = False, stderr = subprocess.STDOUT, stdout = subprocess.PIPE, #creationflags = subprocess.CREATE_NEW_PROCESS_GROUP,
			universal_newlines = True)  #mplayer periodic 'bytes written' string ends with \r
		thr = threading.Thread(target = mplayer_io, args = (info_fpath, proc))
		# thr.daemon = True
		thr.start()

		return nows

	def main ():
		started = False
		cur_stream = None
		start_time_s = None
		while True:
			if not started:
				for n, (name, url, ext) in enumerate(streams, 1):
					print '% 2d' % n, name
			else:
				print "i, ii, rm/del, s H:M, q"
			
			cmd = raw_input(">")
			if (not started) and cmd.isdigit() and (1 <= int(cmd) <= len(streams)):
				cur_stream = streams[int(cmd) - 1]
				sname, stream_url, ext = cur_stream
				start_time_s = start_recording(sname, stream_url, ext)
				started = True
			elif started and (cmd in ('i', 'ii')):
				sname = cur_stream[0]
				mark = {'i': 'imp', 'ii': 'imp2'}[cmd]
				with open('%s/stream_%s_%s_%s' % (dump_dirpath, start_time_s, sname, mark), 'wb') as _:
					pass
				print 'ok'
			elif started and cmd in ('rm', 'del'):
				sname = cur_stream[0]

				must_stop_mplayer[0] = True
				try:
					time.sleep(9000)
					print "@@@ this should not be printed"
				except KeyboardInterrupt:
					pass

				while True:
					if mplayer_exited[0]:
						break
					else:
						time.sleep(0.2)
				
				c = 0
				for fpath in glob.glob('%s/stream_%s_%s*' % (dump_dirpath, start_time_s, sname)):
					os.remove(fpath)
					c += 1
				print 'ok', c, 'deleted'

				raise QuietExit()
			elif started and cmd == 'q':
				#TODO copypasted
				must_stop_mplayer[0] = True
				try:
					time.sleep(9000)
					print "@@@ this should not be printed"
				except KeyboardInterrupt:
					pass

				while True:
					if mplayer_exited[0]:
						break
					else:
						time.sleep(0.2)

				#TODO check that it exited with 0?
				raise QuietExit()
			elif started and cmd.startswith('s '):
				expr = cmd[len('s '):]
				try:
					h, m = map(int, expr.split(':'))
					t = datetime.time(h, m)
				except ValueError:
					print 'input time in format number:number'
					continue
				dt_today = datetime.datetime.combine(datetime.date.today(), t)
				dt_tomor = dt_today + datetime.timedelta(days = 1)
				now = datetime.datetime.now()
				if now > dt_today:
					dt = dt_tomor
				else:
					dt = dt_today
				delay = (dt - now).seconds

				def stop_after ():
					time.sleep(delay)
					must_stop_mplayer[0] = True
				thr = threading.Thread(target = stop_after)
				thr.daemon = True
				thr.start()
				
				print "ok, will stop after %sm" % (delay / 60)
			else:
				#TODO colorize
				print "invalid usage"
			#TODO + edit info?; retry recording on stop (-loop 0 not working?);
	main()


except KeyboardInterrupt:
	print "@@@ KeyboardInterrupt"

#a kludge for windows console
except QuietExit:
	quiet_exit = True
except:
	traceback.print_exc()
finally:
	if not quiet_exit:
		raw_input("@@@ finished")
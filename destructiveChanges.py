#!/usr/bin/env python
import getopt, json, os, sys, StringIO

def main(argv):

	describe_filename, base_dir, git_dir = 'describe.json', 'destructiveChanges', 'github'
	try:
	        opts, args = getopt.getopt(argv,"hf:d:g:",["file=","dir=","git="])
	except getopt.GetoptError:
	        print 'destructiveChanges.py -i <inputfile> -o <outputfile>'
	        sys.exit(2)
	for opt, arg in opts:
	        if opt == '-h':
	                print 'destructiveChanges.py -f <describe.json> -d <destructiveChanges> -g <github>'
	                sys.exit()
	        elif opt in ("-f", "--file"):
	                describe_filename = arg
	        elif opt in ("-d", "--dir"):
	                base_dir = arg
	        elif opt in ("-g", "--git"):
	                git_dir = arg

	describe_file = open(describe_filename, 'r')
	describe = json.load(describe_file)
	describe_file.close()

	if not os.path.exists(base_dir):
		# create the directory
		os.mkdir(base_dir)
		# add an empty packages.xml
		xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
		xml +='<Package xmlns="http://soap.sforce.com/2006/04/metadata">\n'
		xml +='    <version>28.0</version>\n'
		xml +='</Package>'
		package = open(base_dir+'/package.xml', 'w')
		package.write(xml)
		package.close()
	if os.path.exists(base_dir+'/destructiveChanges.xml'):
		os.remove(base_dir+'/destructiveChanges.xml')
	proc = os.popen("diff -rq "+git_dir+"/src/ unpackaged/ | grep 'Only in unpackaged' | grep -v 'meta' | sed 's/Only in unpackaged\/\([^:]*\): \([^\.]*\)\.\(.*\)/\\1,\\3,\\2/g'")
	diffs, metas = proc.read(), []
	buf = StringIO.StringIO(diffs)
	for line in buf.readlines():
		line = line.strip()
		data = line.split(",")
		if data[0] in describe:
			meta = {
				'member': data[2],
				'name':''
			}
			if data[1] in describe[data[0]]:
				meta['name'] = describe[data[0]][data[1]]
			elif '*' in describe[data[0]]:
				meta['name'] = describe[data[0]]['*']
			else:
				continue
			metas.append(meta)
	customfields = []
	proc = os.popen("diff -rqw "+git_dir+"/src/ unpackaged/ | grep 'object differ$' | sed 's/Files \\(.*\\) and \\(.*\\) differ/\\1,\\2/g'")
	diffs, objs = proc.read(), []
	buf = StringIO.StringIO(diffs)
	for line in buf.readlines():
		line = line.strip()
		data = line.split(",")
		git_file, sfdc_file = data[0], data[1]
		class_name = git_file.split("/")[-1].replace('.object', '')
		proc = os.popen("diff "+git_file+" "+sfdc_file+" | grep fullName | grep -v '^<' | sed 's/.*fullName>\(.*\\)<.*/\\1/g'")
		diffs = proc.read()
		buf2 = StringIO.StringIO(diffs);
		for line2 in buf2.readlines():
			line2 = line2.strip()
			customfields.append(class_name+'.'+line2)	

	if len(metas) > 0 or len(customfields) > 0:
		xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
		xml +='<Package xmlns="http://soap.sforce.com/2006/04/metadata">\n'
		if len(metas) > 0:
			for meta in metas:
				xml +='	<types>\n'
				xml +='		<members>'+meta['member']+'</members>\n'
				xml +='		<name>'+meta['name']+'</name>\n'
				xml +='	</types>\n'
		if len(customfields) > 0:
			for field in customfields:
				xml +='	<types>\n'
				xml +='		<members>'+field+'</members>\n'
				xml +='		<name>'+field+'</name>\n'
	    			xml +='	</types>\n'	
		xml +='</Package>'
		destructiveChanges = open(base_dir+'/destructiveChanges.xml', 'w')	
		destructiveChanges.write(xml)
		destructiveChanges.close()
		print "CREATED: destructiveChanges.xml"
		print xml

if  __name__ == '__main__':
    main(sys.argv[1:])
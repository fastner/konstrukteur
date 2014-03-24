from jasy.core.FileManager import FileManager

@task
def build(regenerate = False):
	"""Generate pages"""

	profile = Profile(session)
	profile.registerPart("$${name}", styleName="$${name}.Main")
	profile.setHashAssets(True)
	profile.setCopyAssets(True)

	konstrukteur.build(profile, regenerate)

	Build.run(profile)

	fileManager = FileManager(profile)
	fileManager.updateFile("source/apache.htaccess", "{{destination}}/.htaccess")

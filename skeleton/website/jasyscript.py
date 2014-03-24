from jasy.core.Profile import Profile
import jasy.build.Manager

@task
def build(regenerate = False):
	"""Generate source (development) version"""

	profile = Profile(session)
	profile.registerPart("$${name}", styleName="$${name}.Main")
	profile.setHashAssets(True)
	profile.setCopyAssets(True)

	konstrukteur.build(profile, regenerate)

	Build.run(profile)

	fileManager = FileManager(profile)
	fileManager.updateFile("source/apache.htaccess", "{{destination}}/.htaccess")

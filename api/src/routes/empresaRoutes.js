const { Router } = require('express')
const EmpresaControllers = require('../controllers/EmpresaControllerss')
var auth = require('../service/AutenticaService')
var checkRole = require('../service/checkRole')


const router = Router()
router.post('/register', EmpresaControllers.cadastraUser)

module.exports = router